from .db import SessionLocal, SecurityEvent

INJECTION_PATTERNS = ["ignore previous instructions", "reveal system prompt", "jailbreak"]
EXFIL_PATTERNS = ["api key", "password", "token", "secret"]
ALLOWED_TOOLS = {"calculator", "notes_store"}

def allow_tool_call(goal, tool_name):
    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted", 80
    
    t = (goal or "").lower()
    score = 0
    if any(p in t for p in INJECTION_PATTERNS): score += 60
    if any(p in t for p in EXFIL_PATTERNS): score += 60
    
    risk = min(score, 100)
    if risk >= 60:
        return False, "High-risk goal detected", risk
    return True, "Allowed", risk

def log_event(event_type, goal, tool="", reason="", risk=0):
    db = SessionLocal()
    try:
        event = SecurityEvent(event_type=event_type, tool=tool, reason=reason, risk=risk, goal=goal)
        db.add(event)
        db.commit()
    finally:
        db.close()