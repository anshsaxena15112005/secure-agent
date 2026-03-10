from pathlib import Path
import yaml

from backend.app.db import SessionLocal, SecurityEvent

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_PATH = BASE_DIR / "policies" / "default_policy.yaml"

try:
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        POLICY = yaml.safe_load(f) or {}
except Exception as e:
    print("Failed to load policy file:", e)
    POLICY = {}

INJECTION_PATTERNS = POLICY.get("blocked_patterns", [
    "ignore previous instructions",
    "reveal system prompt",
    "jailbreak",
    "bypass",
])

EXFIL_PATTERNS = POLICY.get("exfiltration_patterns", [
    "api key",
    "password",
    "token",
    "secret",
])

ALLOWED_TOOLS = set(POLICY.get("allowed_tools", ["calculator", "notes_store"]))
BLOCK_THRESHOLD = POLICY.get("block_threshold", 60)

RISK_SCORES = POLICY.get("risk_scores", {
    "prompt_injection": 60,
    "exfiltration": 60,
    "tool_abuse": 80,
})


def risk_score(text: str) -> int:
    t = (text or "").lower()
    score = 0

    if any(p in t for p in INJECTION_PATTERNS):
        score += RISK_SCORES.get("prompt_injection", 60)

    if any(p in t for p in EXFIL_PATTERNS):
        score += RISK_SCORES.get("exfiltration", 60)

    return min(score, 100)


def log_event(event_type: str, goal: str, tool: str = "", reason: str = "", risk: int = 0):
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


def allow_tool_call(goal: str, tool_name: str):
    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted", RISK_SCORES.get("tool_abuse", 80)

    r = risk_score(goal)

    if r >= BLOCK_THRESHOLD:
        return False, "High-risk goal detected", r

    return True, "Allowed", r