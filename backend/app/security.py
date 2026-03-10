from pathlib import Path
import yaml

from app.db import SessionLocal, SecurityEvent


# ------------------------------------------------
# Load Security Policy (YAML)
# ------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_PATH = BASE_DIR / "policies" / "default_policy.yaml"

try:
    with open(POLICY_PATH, "r") as f:
        POLICY = yaml.safe_load(f)
except Exception as e:
    print("Failed to load security policy:", e)
    POLICY = {}


# ------------------------------------------------
# Default patterns (fallback if YAML missing)
# ------------------------------------------------

DEFAULT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "jailbreak",
    "bypass",
    "do anything now",
]

DEFAULT_EXFIL_PATTERNS = [
    "api key",
    "password",
    "secret",
    "token",
    "environment variables",
    "env vars",
    "/etc/passwd",
    "ssh key",
]


# ------------------------------------------------
# Load patterns from YAML or fallback
# ------------------------------------------------

INJECTION_PATTERNS = POLICY.get("blocked_patterns", DEFAULT_INJECTION_PATTERNS)

EXFIL_PATTERNS = POLICY.get("exfiltration_patterns", DEFAULT_EXFIL_PATTERNS)

ALLOWED_TOOLS = set(POLICY.get("allowed_tools", ["calculator", "notes_store"]))

BLOCK_THRESHOLD = POLICY.get("block_threshold", 60)

RISK_SCORES = POLICY.get(
    "risk_scores",
    {
        "prompt_injection": 60,
        "exfiltration": 60,
        "tool_abuse": 80,
    },
)


# ------------------------------------------------
# Risk scoring
# ------------------------------------------------

def risk_score(text: str) -> int:
    """
    Return a risk score from 0 to 100 based on suspicious patterns.
    """

    t = (text or "").lower()
    score = 0

    if any(p in t for p in INJECTION_PATTERNS):
        score += RISK_SCORES.get("prompt_injection", 60)

    if any(p in t for p in EXFIL_PATTERNS):
        score += RISK_SCORES.get("exfiltration", 60)

    return min(score, 100)


# ------------------------------------------------
# Audit Logging
# ------------------------------------------------

def log_event(event_type: str, goal: str, tool: str = "", reason: str = "", risk: int = 0):
    """
    Persist an audit event to SQLite.
    """

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


# ------------------------------------------------
# Tool Authorization
# ------------------------------------------------

def allow_tool_call(goal: str, tool_name: str) -> tuple[bool, str, int]:
    """
    Decide if a tool call is allowed.
    Returns: (allowed, reason, risk)
    """

    # -----------------------------------------
    # 1) Tool allowlist check
    # -----------------------------------------

    if tool_name not in ALLOWED_TOOLS:

        risk = RISK_SCORES.get("tool_abuse", 80)

        log_event(
            event_type="blocked_tool",
            goal=goal,
            tool=tool_name,
            reason="Tool not allowlisted",
            risk=risk,
        )

        return False, "Tool not allowlisted", risk

    # -----------------------------------------
    # 2) Prompt risk check
    # -----------------------------------------

    r = risk_score(goal)

    if r >= BLOCK_THRESHOLD:

        log_event(
            event_type="blocked_prompt",
            goal=goal,
            tool=tool_name,
            reason="High-risk goal detected",
            risk=r,
        )

        return False, "High-risk goal detected (possible prompt injection/exfil)", r

    # -----------------------------------------
    # 3) Allow request
    # -----------------------------------------

    log_event(
        event_type="allowed_request",
        goal=goal,
        tool=tool_name,
        reason="Allowed",
        risk=r,
    )

    return True, "Allowed", r