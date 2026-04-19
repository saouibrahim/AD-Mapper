from neo4j import AsyncSession
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Ingest ──────────────────────────────────────────────────────────────

    async def ingest_domain(self, info: Dict[str, Any]):
        await self.session.run(
            """
            MERGE (d:Domain {name: $name})
            SET d += $props
            """,
            name=info["name"],
            props={k: v for k, v in info.items() if v is not None},
        )

    async def ingest_users(self, users: List[Dict[str, Any]]):
        await self.session.run(
            """
            UNWIND $users AS u
            MERGE (n:User {samAccountName: u.samAccountName})
            SET n += u
            """,
            users=users,
        )
        # Relationships MemberOf
        for user in users:
            for group_dn in user.get("memberOf", []):
                await self.session.run(
                    """
                    MATCH (u:User {samAccountName: $sam})
                    MERGE (g:Group {distinguishedName: $dn})
                    MERGE (u)-[:MEMBER_OF]->(g)
                    """,
                    sam=user["samAccountName"],
                    dn=group_dn,
                )
        # Kerberoastable
        for user in users:
            if user.get("servicePrincipalName"):
                await self.session.run(
                    """
                    MATCH (u:User {samAccountName: $sam})
                    SET u.kerberoastable = true
                    """,
                    sam=user["samAccountName"],
                )

    async def ingest_computers(self, computers: List[Dict[str, Any]]):
        await self.session.run(
            """
            UNWIND $computers AS c
            MERGE (n:Computer {name: c.name})
            SET n += c
            """,
            computers=computers,
        )

    async def ingest_groups(self, groups: List[Dict[str, Any]]):
        for group in groups:
            await self.session.run(
                """
                MERGE (g:Group {name: $name})
                SET g.distinguishedName = $dn,
                    g.description = $desc,
                    g.groupType = $gt
                """,
                name=group["name"],
                dn=group["distinguishedName"],
                desc=group.get("description"),
                gt=group.get("groupType"),
            )
            for member_dn in group.get("members", []):
                await self.session.run(
                    """
                    MERGE (m {distinguishedName: $dn})
                    MERGE (g:Group {name: $gname})
                    MERGE (m)-[:MEMBER_OF]->(g)
                    """,
                    dn=member_dn,
                    gname=group["name"],
                )

    # ── Graph queries ────────────────────────────────────────────────────────

    async def get_full_graph(self) -> Dict[str, Any]:
        result = await self.session.run(
            """
            MATCH (n)
            WHERE n:User OR n:Computer OR n:Group OR n:Domain
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(distinct {
                id: elementId(n),
                label: coalesce(n.samAccountName, n.name, n.distinguishedName, 'inconnu'),
                type: labels(n)[0],
                properties: properties(n)
            }) AS nodes,
            collect(distinct {
                source: elementId(n),
                target: elementId(m),
                relation: type(r)
            }) AS edges
            """
        )
        record = await result.single()
        if not record:
            return {"nodes": [], "edges": []}

        nodes = record["nodes"]
        edges = [e for e in record["edges"] if e["target"] is not None]

        # Compute risk scores
        for node in nodes:
            props = node.get("properties", {})
            score = 0.0
            if node["type"] == "User":
                if props.get("adminCount", 0) == 1:
                    score += 60
                if props.get("kerberoastable"):
                    score += 30
                if not props.get("enabled", True):
                    score -= 20
            elif node["type"] == "Computer":
                os = props.get("operatingSystem", "")
                if os and any(x in os for x in ["2008", "2003", "XP", "Vista", "7"]):
                    score += 50
            elif node["type"] == "Group":
                if any(x in node["label"] for x in ["Admin", "Domain Admins", "Enterprise"]):
                    score += 80
            node["risk_score"] = max(0.0, min(100.0, score))

        return {"nodes": nodes, "edges": edges}

    async def get_attack_paths(self) -> List[Dict[str, Any]]:
        paths = []

        # Path 1: Kerberoastable users → privilege escalation
        result = await self.session.run(
            """
            MATCH (u:User {kerberoastable: true})
            OPTIONAL MATCH (u)-[:MEMBER_OF*1..3]->(g:Group)
            WHERE g.name CONTAINS 'Admin'
            RETURN u, collect(g) AS admin_groups
            """
        )
        async for record in result:
            user = record["u"]
            admin_groups = record["admin_groups"]
            sam = user.get("samAccountName", "?")
            paths.append({
                "id": f"kerb_{sam}",
                "name": f"Kerberoasting → {sam}",
                "severity": "haute" if admin_groups else "moyenne",
                "description": f"L'utilisateur {sam} possède un SPN et est potentiellement Kerberoastable.",
                "nodes": [
                    {"id": f"u_{sam}", "label": sam, "type": "User"},
                ] + [
                    {"id": f"g_{g.get('name', '?')}", "label": g.get("name", "?"), "type": "Group"}
                    for g in admin_groups
                ],
                "edges": [
                    {"source": f"u_{sam}", "target": f"g_{g.get('name', '?')}", "relation": "MEMBER_OF"}
                    for g in admin_groups
                ],
                "steps": [
                    f"1. Demander un ticket TGS pour {sam} (GetUserSPNs.py)",
                    "2. Cracker le hash offline (hashcat -m 13100)",
                    "3. Utiliser les credentials pour accès latéral",
                ],
                "impact": "Compromission de compte privilégié",
                "likelihood": "Haute",
            })

        # Path 2: Admin users
        result2 = await self.session.run(
            """
            MATCH (u:User {adminCount: 1, enabled: true})
            RETURN u LIMIT 20
            """
        )
        async for record in result2:
            user = record["u"]
            sam = user.get("samAccountName", "?")
            paths.append({
                "id": f"admin_{sam}",
                "name": f"Compte Admin Exposé → {sam}",
                "severity": "critique",
                "description": f"{sam} est un compte admin (adminCount=1) actif.",
                "nodes": [{"id": f"u_{sam}", "label": sam, "type": "User"}],
                "edges": [],
                "steps": [
                    f"1. Cibler {sam} via password spray ou phishing",
                    "2. Accès direct aux ressources privilégiées",
                    "3. DCSync / Pass-the-Hash possible",
                ],
                "impact": "Compromission totale du domaine",
                "likelihood": "Moyenne",
            })

        return paths

    async def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        for label, key in [("User", "users"), ("Computer", "computers"), ("Group", "groups"), ("Domain", "domains")]:
            r = await self.session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            rec = await r.single()
            stats[key] = rec["c"] if rec else 0

        r = await self.session.run("MATCH (u:User {adminCount: 1}) RETURN count(u) AS c")
        rec = await r.single()
        stats["admin_users"] = rec["c"] if rec else 0

        r = await self.session.run("MATCH (u:User {kerberoastable: true}) RETURN count(u) AS c")
        rec = await r.single()
        stats["kerberoastable"] = rec["c"] if rec else 0

        r = await self.session.run("MATCH (u:User {enabled: false}) RETURN count(u) AS c")
        rec = await r.single()
        stats["disabled_users"] = rec["c"] if rec else 0

        return stats

    async def clear_graph(self):
        await self.session.run("MATCH (n) DETACH DELETE n")
