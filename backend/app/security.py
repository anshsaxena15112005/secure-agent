from pathlib import Path
import yaml

from backend.app.db import SessionLocal, SecurityEvent

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_PATH = BASE_DIR / "policies" / "default_policy.yaml"

try:
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        POLICY = yaml.safe_load(f) or {}
    POLICY_LOADED = True
except Exception as e:
    print("Failed to load policy file:", e)
    POLICY = {}
    POLICY_LOADED = False

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
ROLE_CONFIG = POLICY.get("roles", {})

BLOCK_THRESHOLD = POLICY.get("block_threshold", 60)

RISK_SCORES = POLICY.get("risk_scores", {
    "prompt_injection": 60,
    "exfiltration": 60,
    "tool_abuse": 80,
    "role_violation": 70,
})


def severity_from_risk(risk: int) -> str:
    if risk >= 85:
        return "critical"
    if risk >= 60:
        return "high"
    if risk >= 30:
        return "medium"
    return "low"


def risk_score(text: str) -> int:
    t = (text or "").lower()
    score = 0

    if any(p in t for p in INJECTION_PATTERNS):
        score += RISK_SCORES.get("prompt_injection", 60)

    if any(p in t for p in EXFIL_PATTERNS):
        score += RISK_SCORES.get("exfiltration", 60)

    return min(score, 100)


def is_tool_allowed_for_role(role: str, tool_name: str) -> bool:
    role_policy = ROLE_CONFIG.get(role, {})
    allowed_tools = set(role_policy.get("allowed_tools", []))
    return tool_name in allowed_tools


def log_event(
    event_type: str,
    goal: str,
    tool: str = "",
    reason: str = "",
    risk: int = 0,
    app_id: str = "default-app",
    role: str = "user",
):
    severity = severity_from_risk(risk)

    db = SessionLocal()
    try:
        db.add(
            SecurityEvent(
                app_id=app_id,
                role=role,
                event_type=event_type,
                severity=severity,
                tool=tool,
                reason=reason,
                risk=risk,
                goal=goal,
            )
        )
        db.commit()
    finally:
        db.close()


def allow_tool_call(goal: str, tool_name: str, role: str = "user"):
    # global allowlist
    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted globally", RISK_SCORES.get("tool_abuse", 80)

    # role-based allowlist
    if not is_tool_allowed_for_role(role, tool_name):
        return False, f"Role '{role}' is not permitted to use tool '{tool_name}'", RISK_SCORES.get("role_violation", 70)

    # prompt risk
    r = risk_score(goal)
    if r >= BLOCK_THRESHOLD:
        return False, "High-risk goal detected", r

    return True, "Allowed", r


def get_policy_status():
    return {
        "policy_loaded": POLICY_LOADED,
        "policy_path": str(POLICY_PATH),
        "blocked_patterns_count": len(INJECTION_PATTERNS),
        "exfiltration_patterns_count": len(EXFIL_PATTERNS),
        "allowed_tools": sorted(list(ALLOWED_TOOLS)),
        "roles": ROLE_CONFIG,
        "block_threshold": BLOCK_THRESHOLD,
        "risk_scores": RISK_SCORES,
    }