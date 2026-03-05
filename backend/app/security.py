from app.db import SessionLocal, SecurityEvent

# --- Simple detectors (MVP) ---
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "jailbreak",
    "bypass",
    "do anything now",
]

EXFIL_PATTERNS = [
    "api key",
    "password",
    "secret",
    "token",
    "environment variables",
    "env vars",
    "/etc/passwd",
    "ssh key",
]

# Only allow these tools in Phase 1
ALLOWED_TOOLS = {"calculator", "notes_store"}

# If risk >= this, block
BLOCK_THRESHOLD = 60


def risk_score(text: str) -> int:
    """Return a risk score from 0 to 100 based on suspicious patterns."""
    t = (text or "").lower()
    score = 0

    if any(p in t for p in INJECTION_PATTERNS):
        score += 60

    if any(p in t for p in EXFIL_PATTERNS):
        score += 60

    return min(score, 100)


def log_event(event_type: str, goal: str, tool: str = "", reason: str = "", risk: int = 0):
    """Persist an audit event to SQLite."""
    db = SessionLocal()
    try:
        db.add(
            SecurityEvent(
                event_type=event_type,
                tool=tool,
                reason=reason,
                risk=risk,
                goal=goal,
            )
        )
        db.commit()
    finally:
        db.close()


def allow_tool_call(goal: str, tool_name: str) -> tuple[bool, str, int]:
    """
    Decide if a tool call is allowed.
    Returns: (allowed, reason, risk)
    """
    # 1) Tool allowlist check
    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted", 80

    # 2) Prompt risk check
    r = risk_score(goal)
    if r >= BLOCK_THRESHOLD:
        return False, "High-risk goal detected (possible prompt injection/exfil)", r

    return True, "Allowed", r