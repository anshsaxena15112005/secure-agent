from backend.app.db import SessionLocal, SecurityEvent

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "jailbreak",
    "bypass",
]

EXFIL_PATTERNS = [
    "api key",
    "password",
    "secret",
    "token",
]

ALLOWED_TOOLS = {"calculator", "notes_store"}

BLOCK_THRESHOLD = 60


def risk_score(text: str):

    t = (text or "").lower()
    score = 0

    if any(p in t for p in INJECTION_PATTERNS):
        score += 60

    if any(p in t for p in EXFIL_PATTERNS):
        score += 60

    return min(score, 100)


def log_event(event_type, goal, tool="", reason="", risk=0):

    db = SessionLocal()

    try:
        db.add(
            SecurityEvent(
                event_type=event_type,
                tool=tool,
                reason=reason,
                risk=risk,
                goal=goal
            )
        )

        db.commit()

    finally:
        db.close()


def allow_tool_call(goal: str, tool_name: str):

    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted", 80

    r = risk_score(goal)

    if r >= BLOCK_THRESHOLD:
        return False, "High-risk goal detected", r

    return True, "Allowed", r