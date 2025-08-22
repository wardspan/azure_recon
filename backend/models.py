from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class AuthResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int

class AuthStatus(BaseModel):
    authenticated: bool
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None

class PasswordLoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: str

class ServicePrincipalLoginRequest(BaseModel):
    client_id: str
    client_secret: str
    tenant_id: str

class SecureScoreData(BaseModel):
    current_score: float
    max_score: float
    percentage: float
    control_scores: List[Dict[str, Any]]

class Recommendation(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    category: str
    state: str
    affected_resources: int

class PublicResource(BaseModel):
    resource_id: str
    resource_name: str
    resource_type: str
    public_ip: Optional[str] = None
    ports: List[int]
    protocols: List[str]
    subscription_id: str
    resource_group: str

class NetworkSecurityGroup(BaseModel):
    id: str
    name: str
    location: str
    resource_group: str
    subscription_id: str
    rules: List[Dict[str, Any]]
    risk_level: str
    risky_rules: Optional[List[Dict[str, Any]]] = []
    risk_reasons: Optional[List[str]] = []

class UserInfo(BaseModel):
    id: str
    display_name: str
    user_principal_name: str
    mail: Optional[str]
    is_guest: bool
    mfa_enabled: bool
    sign_in_activity: Optional[Dict[str, Any]]

class RoleAssignment(BaseModel):
    principal_id: str
    principal_name: str
    principal_type: str
    role_definition_name: str
    scope: str
    subscription_id: Optional[str]

class PolicyAssignment(BaseModel):
    id: str
    name: str
    display_name: str
    policy_definition_id: str
    scope: str
    enforcement_mode: str
    compliance_state: Optional[str]

class ComplianceResult(BaseModel):
    policy_assignment_id: str
    policy_assignment_name: str
    resource_id: str
    compliance_state: str
    resource_type: str
    resource_location: str

class ScanResult(BaseModel):
    tenant_id: str
    scan_timestamp: datetime
    secure_score: SecureScoreData
    recommendations: List[Recommendation]
    public_resources: List[PublicResource]
    network_security_groups: List[NetworkSecurityGroup]
    users: List[UserInfo]
    role_assignments: List[RoleAssignment]
    policy_assignments: List[PolicyAssignment]
    compliance_results: List[ComplianceResult]

class ReportRequest(BaseModel):
    format: str  # "markdown" or "pdf"
    scan_id: Optional[str] = None

class Subscription(BaseModel):
    subscription_id: str
    display_name: str
    state: str
    tenant_id: str