import ldap3
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

WINDOWS_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def filetime_to_dt(filetime: int) -> Optional[str]:
    if filetime in (0, 9223372036854775807):
        return None
    try:
        delta_seconds = filetime / 10_000_000
        dt = datetime.fromtimestamp(delta_seconds - 11644473600, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


class ADReconService:
    def __init__(self, dc_host: str, domain: str, username: str, password: str,
                 port: int = 389, use_ssl: bool = False):
        self.dc_host = dc_host
        self.domain = domain
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.base_dn = ",".join(f"DC={part}" for part in domain.split("."))
        self.conn: Optional[Connection] = None

    def connect(self) -> bool:
        try:
            server = Server(self.dc_host, port=self.port, use_ssl=self.use_ssl,
                            get_info=ALL, connect_timeout=10)
            self.conn = Connection(
                server,
                user=f"{self.domain}\\{self.username}",
                password=self.password,
                authentication=NTLM,
                auto_bind=True,
            )
            logger.info(f"Connecté à {self.dc_host} ({self.domain})")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion LDAP: {e}")
            raise ConnectionError(f"Impossible de se connecter à {self.dc_host}: {e}")

    def disconnect(self):
        if self.conn:
            self.conn.unbind()

    def _search(self, search_filter: str, attributes: List[str]) -> List[Dict[str, Any]]:
        if not self.conn:
            raise RuntimeError("Non connecté")
        self.conn.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes,
        )
        results = []
        for entry in self.conn.entries:
            obj = {"dn": entry.entry_dn}
            for attr in attributes:
                try:
                    val = entry[attr].value
                    obj[attr] = val
                except Exception:
                    obj[attr] = None
            results.append(obj)
        return results

    def enumerate_users(self) -> List[Dict[str, Any]]:
        attrs = [
            "sAMAccountName", "distinguishedName", "displayName", "mail",
            "userAccountControl", "adminCount", "memberOf", "lastLogon",
            "pwdLastSet", "description", "servicePrincipalName",
            "objectSid", "whenCreated",
        ]
        entries = self._search("(&(objectCategory=person)(objectClass=user))", attrs)
        users = []
        for e in entries:
            uac = e.get("userAccountControl") or 0
            enabled = not bool(uac & 2) if uac else True
            spn = e.get("servicePrincipalName") or []
            if isinstance(spn, str):
                spn = [spn]
            memberof = e.get("memberOf") or []
            if isinstance(memberof, str):
                memberof = [memberof]
            users.append({
                "samAccountName": e.get("sAMAccountName") or "",
                "distinguishedName": e.get("distinguishedName") or e["dn"],
                "displayName": e.get("displayName"),
                "mail": e.get("mail"),
                "enabled": enabled,
                "adminCount": int(e.get("adminCount") or 0),
                "memberOf": memberof,
                "lastLogon": filetime_to_dt(e.get("lastLogon") or 0),
                "pwdLastSet": filetime_to_dt(e.get("pwdLastSet") or 0),
                "description": e.get("description"),
                "servicePrincipalName": spn,
            })
        return users

    def enumerate_computers(self) -> List[Dict[str, Any]]:
        attrs = [
            "name", "distinguishedName", "operatingSystem",
            "operatingSystemVersion", "userAccountControl",
            "lastLogonTimestamp", "dNSHostName", "objectSid",
        ]
        entries = self._search("(objectClass=computer)", attrs)
        computers = []
        for e in entries:
            uac = e.get("userAccountControl") or 0
            enabled = not bool(uac & 2) if uac else True
            computers.append({
                "name": e.get("name") or "",
                "distinguishedName": e.get("distinguishedName") or e["dn"],
                "operatingSystem": e.get("operatingSystem"),
                "operatingSystemVersion": e.get("operatingSystemVersion"),
                "enabled": enabled,
                "lastLogonTimestamp": filetime_to_dt(e.get("lastLogonTimestamp") or 0),
                "dnsHostName": e.get("dNSHostName"),
            })
        return computers

    def enumerate_groups(self) -> List[Dict[str, Any]]:
        attrs = ["name", "distinguishedName", "description", "member", "groupType"]
        entries = self._search("(objectClass=group)", attrs)
        groups = []
        for e in entries:
            members = e.get("member") or []
            if isinstance(members, str):
                members = [members]
            gt = e.get("groupType") or 0
            if isinstance(gt, int):
                if gt & 0x80000000:
                    group_type = "Sécurité"
                else:
                    group_type = "Distribution"
            else:
                group_type = str(gt)
            groups.append({
                "name": e.get("name") or "",
                "distinguishedName": e.get("distinguishedName") or e["dn"],
                "description": e.get("description"),
                "members": members,
                "groupType": group_type,
            })
        return groups

    def enumerate_ous(self) -> List[Dict[str, Any]]:
        attrs = ["name", "distinguishedName", "description", "gpLink"]
        entries = self._search("(objectClass=organizationalUnit)", attrs)
        ous = []
        for e in entries:
            ous.append({
                "name": e.get("name") or "",
                "distinguishedName": e.get("distinguishedName") or e["dn"],
                "description": e.get("description"),
                "gpLink": e.get("gpLink"),
            })
        return ous

    def get_domain_info(self) -> Dict[str, Any]:
        attrs = [
            "name", "distinguishedName", "whenCreated",
            "msDS-Behavior-Version", "objectSid", "domainFunctionality",
        ]
        entries = self._search("(objectClass=domain)", attrs)
        if entries:
            e = entries[0]
            return {
                "name": self.domain,
                "distinguishedName": e.get("distinguishedName") or self.base_dn,
                "functionalLevel": str(e.get("msDS-Behavior-Version") or "Inconnu"),
            }
        return {"name": self.domain, "distinguishedName": self.base_dn}
