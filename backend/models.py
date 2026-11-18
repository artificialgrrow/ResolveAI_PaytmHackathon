from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LoginRequest(BaseModel):
    username: str
    password: str

class MerchantProfile(BaseModel):
    id: str
    name: str
    username: str
    business_type: str
    bank_name: str
    account_number: str
    ifsc: str
    phone: str

class IncidentRequest(BaseModel):
    merchant_id: str
    message: str
    scenario_hint: Optional[str] = None
    language: Optional[str] = "en"

class ApprovalRequest(BaseModel):
    incident_id: str
    approved: bool
    notes: Optional[str] = None
    language: Optional[str] = "en"

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"

class AgentEvent(BaseModel):
    step: int
    agent: str # e.g. 'Manager', 'Investigator', 'Remediation', 'Verification'
    status: str # 'THINKING', 'TOOL_CALL', 'SUCCESS', 'AWAITING_APPROVAL', 'ESCALATED'
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str

class IncidentResponse(BaseModel):
    incident_id: str
    merchant_id: str
    status: str # 'RESOLVED', 'AWAITING_APPROVAL', 'ESCALATED', 'FAILED'
    final_message: str
    utr_number: Optional[str] = None
    requires_approval: bool = False
    approval_amount: Optional[float] = None
    approval_reason: Optional[str] = None
    events: List[AgentEvent] = []

class StegoGenerateRequest(BaseModel):
    merchant_id: str

class StegoVerifyRequest(BaseModel):
    merchant_id: str
    image_base64: str


class QRVoiceRequest(BaseModel):
    merchant_id: str = "M-101"
    query: str = "Is this QR valid?"
    language: Optional[str] = "en"
    is_verified: bool = False
    is_valid: Optional[bool] = None
    integrity_score: Optional[float] = None
    scanned_vpa: Optional[str] = None
