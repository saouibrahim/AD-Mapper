from neo4j import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class MisconfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_all(self) -> List[Dict[str, Any]]:
        findings = []
        findings += await self._kerberoastable_admins()
        findings += await self._disabled_admin_accounts()
        findings += await self._never_logged_admins()
        findings += await self._old_password_accounts()
        findings += await self._empty_description_admins()
        findings += await self._legacy_os_computers()
        findings += await self._privileged_groups_large()
        findings += await self._stale_computers()
        return findings

    async def _kerberoastable_admins(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            "MATCH (u:User {kerberoastable: true, adminCount: 1}) RETURN u"
        )
        affected = []
        async for record in result:
            affected.append(record["u"].get("samAccountName", "?"))
        if not affected:
            return []
        return [{
            "id": "KERB_ADMIN_001",
            "type": "kerberoasting",
            "severity": "critique",
            "title": "Comptes admin Kerberoastables",
            "description": "Des comptes avec adminCount=1 possèdent un SPN, rendant possible l'attaque Kerberoasting pour obtenir leurs credentials.",
            "affected_objects": affected,
            "evidence": {"count": len(affected), "technique": "Kerberoasting (T1558.003)"},
            "recommendation": "Supprimer les SPN inutiles des comptes admin. Utiliser des MSA/gMSA à la place.",
            "cvss_score": 8.8,
        }]

    async def _disabled_admin_accounts(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            "MATCH (u:User {adminCount: 1, enabled: false}) RETURN u"
        )
        affected = []
        async for record in result:
            affected.append(record["u"].get("samAccountName", "?"))
        if not affected:
            return []
        return [{
            "id": "ADMIN_DISABLED_002",
            "type": "compte_fantome",
            "severity": "haute",
            "title": "Comptes admin désactivés avec adminCount=1",
            "description": "Ces comptes désactivés conservent l'attribut adminCount=1, réduisant leur visibilité mais maintenant leurs ACL. Un attaquant pourrait les réactiver.",
            "affected_objects": affected,
            "evidence": {"count": len(affected)},
            "recommendation": "Nettoyer l'attribut adminCount sur les comptes désactivés et auditer leurs ACL.",
            "cvss_score": 6.5,
        }]

    async def _never_logged_admins(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            "MATCH (u:User {adminCount: 1}) WHERE u.lastLogon IS NULL OR u.lastLogon = '' RETURN u"
        )
        affected = []
        async for record in result:
            affected.append(record["u"].get("samAccountName", "?"))
        if not affected:
            return []
        return [{
            "id": "ADMIN_STALE_003",
            "type": "compte_fantome",
            "severity": "haute",
            "title": "Comptes admin sans historique de connexion",
            "description": "Comptes privilégiés n'ayant jamais été utilisés ou dont le lastLogon n'est pas renseigné. Vecteur d'attaque par réactivation.",
            "affected_objects": affected,
            "evidence": {"count": len(affected)},
            "recommendation": "Désactiver ou supprimer ces comptes après audit. Mettre en place un processus de revue des comptes orphelins.",
            "cvss_score": 5.5,
        }]

    async def _old_password_accounts(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            """
            MATCH (u:User {enabled: true})
            WHERE u.pwdLastSet IS NOT NULL AND u.pwdLastSet <> ''
            RETURN u.samAccountName AS sam, u.pwdLastSet AS pls
            """
        )
        affected = []
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        async for record in result:
            pls = record.get("pls")
            if pls and pls < cutoff:
                affected.append(record["sam"])
        if not affected:
            return []
        return [{
            "id": "PWD_OLD_004",
            "type": "politique_mdp",
            "severity": "moyenne",
            "title": "Comptes actifs avec mot de passe > 1 an",
            "description": f"{len(affected)} comptes actifs n'ont pas changé de mot de passe depuis plus d'un an.",
            "affected_objects": affected[:20],
            "evidence": {"count": len(affected), "seuil_jours": 365},
            "recommendation": "Appliquer une politique de renouvellement de mots de passe. Forcer le changement pour ces comptes.",
            "cvss_score": 5.0,
        }]

    async def _empty_description_admins(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            """
            MATCH (u:User {adminCount: 1})
            WHERE u.description IS NOT NULL AND u.description <> ''
            RETURN u.samAccountName AS sam, u.description AS desc
            """
        )
        affected = []
        async for record in result:
            affected.append(f"{record['sam']}: {record['desc']}")
        if not affected:
            return []
        return [{
            "id": "DESC_LEAK_005",
            "type": "fuite_info",
            "severity": "basse",
            "title": "Descriptions sensibles sur comptes admin",
            "description": "Des comptes admin ont des descriptions lisibles via LDAP sans authentification élevée, pouvant révéler des informations sur les rôles.",
            "affected_objects": affected,
            "evidence": {"count": len(affected)},
            "recommendation": "Vider ou anonymiser les descriptions des comptes admin.",
            "cvss_score": 3.1,
        }]

    async def _legacy_os_computers(self) -> List[Dict[str, Any]]:
        legacy = ["Windows XP", "Windows Vista", "Windows 7", "Server 2003", "Server 2008"]
        result = await self.session.run(
            "MATCH (c:Computer) WHERE c.operatingSystem IS NOT NULL RETURN c.name AS name, c.operatingSystem AS os"
        )
        affected = []
        async for record in result:
            os = record.get("os") or ""
            if any(l in os for l in legacy):
                affected.append(f"{record['name']} ({os})")
        if not affected:
            return []
        return [{
            "id": "LEGACY_OS_006",
            "type": "systeme_obsolete",
            "severity": "critique",
            "title": "Systèmes d'exploitation obsolètes détectés",
            "description": "Des machines tournent sous des OS hors support (EOL), exposées à des vulnérabilités non patchées (EternalBlue, etc.).",
            "affected_objects": affected,
            "evidence": {"count": len(affected), "technique": "Exploit public (T1190)"},
            "recommendation": "Migrer immédiatement vers des OS supportés ou isoler ces machines en VLAN dédié.",
            "cvss_score": 9.8,
        }]

    async def _privileged_groups_large(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            """
            MATCH (g:Group)-[:MEMBER_OF*0..1]-(u:User)
            WHERE g.name IN ['Domain Admins', 'Enterprise Admins', 'Schema Admins', 'Administrators']
            RETURN g.name AS gname, count(u) AS cnt
            """
        )
        findings = []
        async for record in result:
            if record["cnt"] > 5:
                findings.append({
                    "id": f"PRIV_GROUP_{record['gname'].replace(' ', '_')}",
                    "type": "droits_excessifs",
                    "severity": "haute",
                    "title": f"Groupe privilégié surchargé: {record['gname']}",
                    "description": f"Le groupe {record['gname']} contient {record['cnt']} membres, augmentant la surface d'attaque.",
                    "affected_objects": [record["gname"]],
                    "evidence": {"members_count": record["cnt"]},
                    "recommendation": f"Réduire le groupe {record['gname']} au strict minimum. Utiliser des groupes dédiés par fonction.",
                    "cvss_score": 7.2,
                })
        return findings

    async def _stale_computers(self) -> List[Dict[str, Any]]:
        result = await self.session.run(
            """
            MATCH (c:Computer {enabled: true})
            WHERE c.lastLogonTimestamp IS NOT NULL AND c.lastLogonTimestamp <> ''
            RETURN c.name AS name, c.lastLogonTimestamp AS ts
            """
        )
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        affected = []
        async for record in result:
            ts = record.get("ts")
            if ts and ts < cutoff:
                affected.append(record["name"])
        if not affected:
            return []
        return [{
            "id": "STALE_COMPUTER_007",
            "type": "machine_fantome",
            "severity": "moyenne",
            "title": "Machines inactives depuis > 90 jours",
            "description": f"{len(affected)} machines actives dans l'AD n'ont pas eu de connexion récente. Peuvent représenter des cibles non patchées.",
            "affected_objects": affected[:20],
            "evidence": {"count": len(affected), "seuil_jours": 90},
            "recommendation": "Désactiver ou supprimer les objets machine inactifs. Revue trimestrielle recommandée.",
            "cvss_score": 4.0,
        }]
