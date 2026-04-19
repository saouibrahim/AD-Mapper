from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    CRITIQUE = "critique"
    HAUTE = "haute"
    MOYENNE = "moyenne"
    BASSE = "basse"
    INFO = "info"


class ReconTarget(BaseModel):
    dc_host: str
    domain: str
    username: str
    password: str
    use_kerberos: bool = False
    ldap_port: int = 389
    use_ssl: bool = False


class ADUser(BaseModel):
    samAccountName: str
    distinguishedName: str
    displayName: Optional[str] = None
    mail: Optional[str] = None
    enabled: bool = True
    adminCount: int = 0
    memberOf: List[str] = []
    lastLogon: Optional[str] = None
    pwdLastSet: Optional[str] = None
    description: Optional[str] = None
    servicePrincipalName: List[str] = []


class ADComputer(BaseModel):
    name: str
    distinguishedName: str
    operatingSystem: Optional[str] = None
    operatingSystemVersion: Optional[str] = None
    enabled: bool = True
    lastLogonTimestamp: Optional[str] = None
    dnsHostName: Optional[str] = None


class ADGroup(BaseModel):
    name: str
    distinguishedName: str
    description: Optional[str] = None
    members: List[str] = []
    groupType: Optional[str] = None


class ADACL(BaseModel):
    objectDN: str
    principalSID: str
    principalName: Optional[str] = None
    rights: List[str] = []
    aceType: str
    isInherited: bool = False


class Misconfiguration(BaseModel):
    id: str
    type: str
    severity: Severity
    title: str
    description: str
    affected_objects: List[str] = []
    evidence: Dict[str, Any] = {}
    recommendation: str
    cvss_score: Optional[float] = None


class AttackPath(BaseModel):
    id: str
    name: str
    severity: Severity
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    description: str
    steps: List[str] = []
    impact: str
    likelihood: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # User, Computer, Group, Domain, OU
    properties: Dict[str, Any] = {}
    risk_score: float = 0.0


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # MemberOf, AdminTo, HasSPN, CanRDP, etc.
    properties: Dict[str, Any] = {}


class ReportRequest(BaseModel):
    title: str
    mission: Optional[str] = None
    operator: Optional[str] = None
    include_graph: bool = True
    include_misconfigs: bool = True
    include_paths: bool = True
    severity_filter: List[Severity] = []


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str
