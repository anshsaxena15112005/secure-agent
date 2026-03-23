from pathlib import Path
import re
import yaml

from backend.app.db import SessionLocal, SecurityEvent, Incident

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

OUTPUT_SENSITIVE_PATTERNS = POLICY.get("output_sensitive_patterns", [
    "api key",
    "password",
    "secret",
    "token",
    "sk-",
    "bearer",
    "private key",
])

OUTPUT_ACTION = POLICY.get("output_action", "redact")

ALLOWED_TOOLS = set(POLICY.get("allowed_tools", ["calculator", "notes_store"]))
ROLE_CONFIG = POLICY.get("roles", {})

BLOCK_THRESHOLD = POLICY.get("block_threshold", 60)

RISK_SCORES = POLICY.get("risk_scores", {
    "prompt_injection": 60,
    "exfiltration": 60,
    "tool_abuse": 80,
    "role_violation": 70,
    "output_leakage": 75,
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


def create_incident_if_needed(
    app_id: str,
    role: str,
    event_type: str,
    severity: str,
    tool: str,
    reason: str,
    risk: int,
    goal: str,
):
    if severity not in {"high", "critical"}:
        return

    if event_type not in {"PROMPT_BLOCKED", "TOOL_BLOCKED", "OUTPUT_BLOCKED", "OUTPUT_REDACTED"}:
        return

    db = SessionLocal()
    try:
        incident = Incident(
            app_id=app_id,
            role=role,
            event_type=event_type,
            severity=severity,
            tool=tool,
            reason=reason,
            risk=risk,
            goal=goal,
            status="open",
        )
        db.add(incident)
        db.commit()
    finally:
        db.close()


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

    create_incident_if_needed(
        app_id=app_id,
        role=role,
        event_type=event_type,
        severity=severity,
        tool=tool,
        reason=reason,
        risk=risk,
        goal=goal,
    )


def allow_tool_call(goal: str, tool_name: str, role: str = "user"):
    if tool_name not in ALLOWED_TOOLS:
        return False, "Tool not allowlisted globally", RISK_SCORES.get("tool_abuse", 80)

    if not is_tool_allowed_for_role(role, tool_name):
        return False, f"Role '{role}' is not permitted to use tool '{tool_name}'", RISK_SCORES.get("role_violation", 70)

    r = risk_score(goal)
    if r >= BLOCK_THRESHOLD:
        return False, "High-risk goal detected", r

    return True, "Allowed", r


def inspect_output(output, app_id: str, role: str, tool: str, goal: str):
    """
    Returns:
      {
        "status": "safe" | "redacted" | "blocked",
        "output": ...,
        "reason": "...",
        "risk": int
      }
    """
    output_text = str(output).lower()

    matched = [p for p in OUTPUT_SENSITIVE_PATTERNS if p in output_text]
    if not matched:
        return {
            "status": "safe",
            "output": output,
            "reason": "Output passed inspection",
            "risk": 0,
        }

    risk = RISK_SCORES.get("output_leakage", 75)
    reason = f"Sensitive output detected: {', '.join(matched)}"

    if OUTPUT_ACTION == "block":
        log_event(
            event_type="OUTPUT_BLOCKED",
            goal=goal,
            tool=tool,
            reason=reason,
            risk=risk,
            app_id=app_id,
            role=role,
        )
        return {
            "status": "blocked",
            "output": "[BLOCKED: sensitive output detected]",
            "reason": reason,
            "risk": risk,
        }

    redacted = str(output)
    for pattern in matched:
        redacted = re.sub(re.escape(pattern), "[REDACTED]", redacted, flags=re.IGNORECASE)

    log_event(
        event_type="OUTPUT_REDACTED",
        goal=goal,
        tool=tool,
        reason=reason,
        risk=risk,
        app_id=app_id,
        role=role,
    )

    return {
        "status": "redacted",
        "output": redacted,
        "reason": reason,
        "risk": risk,
    }


def get_policy_status():
    return {
        "policy_loaded": POLICY_LOADED,
        "policy_path": str(POLICY_PATH),
        "blocked_patterns_count": len(INJECTION_PATTERNS),
        "exfiltration_patterns_count": len(EXFIL_PATTERNS),
        "output_sensitive_patterns_count": len(OUTPUT_SENSITIVE_PATTERNS),
        "output_action": OUTPUT_ACTION,
        "allowed_tools": sorted(list(ALLOWED_TOOLS)),
        "roles": ROLE_CONFIG,
        "block_threshold": BLOCK_THRESHOLD,
        "risk_scores": RISK_SCORES,
    }