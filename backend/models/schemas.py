from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    username: str
    role: str


class AgentStatusContext(BaseModel):
    status: str
    uptime_seconds: int


class PolicyEvaluationRequest(BaseModel):
    action: str
    resource: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class PolicyEvaluationResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class AgentRunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model_name: Optional[str] = "mock"
    tool_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentRunResponse(BaseModel):
    status: str
    prompt: str
    response: str
    blocked: bool
    risk_score: int
    reason: Optional[str] = None
    model_name: Optional[str] = None
    tool_name: Optional[str] = None
    incident_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class IncidentResponse(BaseModel):
    id: int
    severity: str
    category: str
    message: str
    blocked: bool
    timestamp: Optional[str] = None
    source: Optional[str] = None


class ReportSummaryResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    total_incidents: int
    high_risk_count: int


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str