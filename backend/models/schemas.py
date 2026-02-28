from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AgentStatusContext(BaseModel):
    status: str
    uptime_seconds: int

class PolicyEvaluationRequest(BaseModel):
    action: str
    resource: str
    context: Optional[Dict[str, Any]] = None

class PolicyEvaluationResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
