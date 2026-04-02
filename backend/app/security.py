import re
from typing import Dict, Any, List, Optional

from backend.app.policy_loader import get_policy

policy = get_policy()

PROMPT_INJECTION_PATTERNS = policy.get("prompt_injection_patterns", [])
SECRET_PATTERNS = policy.get("secret_patterns", [])
PII_PATTERNS = policy.get("pii_patterns", [])

BLOCKED_TOOLS = set(policy.get("blocked_tools", []))
HIGH_RISK_TOOLS = set(policy.get("high_risk_tools", []))

RISK_CONFIG = policy.get("risk_thresholds", {})
BLOCK_THRESHOLD = RISK_CONFIG.get("block", 60)
CRITICAL_THRESHOLD = RISK_CONFIG.get("critical", 80)
OUTPUT_BLOCK_THRESHOLD = RISK_CONFIG.get("output_block", 70)
OUTPUT_REDACT_THRESHOLD = RISK_CONFIG.get("output_redact", 30)

ROLE_POLICIES = policy.get("roles", {})


def _match_patterns(text: str, patterns: List[str]) -> List[str]:
    matches = []
    source_text = text or ""

    for pattern in patterns:
        try:
            if re.search(pattern, source_text, flags=re.IGNORECASE):
                matches.append(pattern)
        except re.error:
            if pattern.lower() in source_text.lower():
                matches.append(pattern)

    return matches


def _calculate_severity(risk: int) -> str:
    if risk >= CRITICAL_THRESHOLD:
        return "critical"
    if risk >= BLOCK_THRESHOLD:
        return "high"
    if risk >= 30:
        return "medium"
    return "low"


def analyze_prompt(text: str) -> Dict[str, Any]:
    prompt = text or ""
    matched_injection = _match_patterns(prompt, PROMPT_INJECTION_PATTERNS)
    matched_secrets = _match_patterns(prompt, SECRET_PATTERNS)
    matched_pii = _match_patterns(prompt, PII_PATTERNS)

    risk = 0
    reasons = []

    if matched_injection:
        risk += 50
        reasons.append("Prompt injection indicators detected")

    if matched_secrets:
        risk += 30
        reasons.append("Secret extraction indicators detected")

    if matched_pii:
        risk += 20
        reasons.append("Possible PII pattern detected")

    risk = min(risk, 100)
    severity = _calculate_severity(risk)
    blocked = risk >= BLOCK_THRESHOLD

    return {
        "blocked": blocked,
        "risk": risk,
        "severity": severity,
        "reasons": reasons,
        "matches": {
            "prompt_injection": matched_injection,
            "secrets": matched_secrets,
            "pii": matched_pii,
        },
    }


def evaluate_tool_use(tool_name: str, role: Optional[str] = None) -> Dict[str, Any]:
    tool = (tool_name or "").strip().lower()
    user_role = (role or "").strip().lower()

    if tool in BLOCKED_TOOLS:
        return {
            "allowed": False,
            "risk": 90,
            "severity": "critical",
            "reason": f"Tool '{tool}' is blocked by policy",
        }

    if user_role:
        role_config = ROLE_POLICIES.get(user_role, {})
        allowed_tools = set(role_config.get("allowed_tools", []))

        if allowed_tools and tool not in allowed_tools and tool != "none":
            return {
                "allowed": False,
                "risk": 75,
                "severity": "high",
                "reason": f"Tool '{tool}' is not allowed for role '{user_role}'",
            }

    if tool in HIGH_RISK_TOOLS:
        return {
            "allowed": True,
            "risk": 50,
            "severity": "medium",
            "reason": f"Tool '{tool}' is high-risk and must be monitored",
        }

    return {
        "allowed": True,
        "risk": 5,
        "severity": "low",
        "reason": f"Tool '{tool}' allowed",
    }


def inspect_output(text: str) -> Dict[str, Any]:
    output = text or ""
    matched_secrets = _match_patterns(output, SECRET_PATTERNS)
    matched_pii = _match_patterns(output, PII_PATTERNS)

    risk = 0
    reasons = []

    if matched_secrets:
        risk += 50
        reasons.append("Sensitive secret-like content detected in output")

    if matched_pii:
        risk += 25
        reasons.append("Possible PII detected in output")

    risk = min(risk, 100)

    if risk >= OUTPUT_BLOCK_THRESHOLD:
        severity = "high"
    elif risk >= OUTPUT_REDACT_THRESHOLD:
        severity = "medium"
    else:
        severity = "low"

    should_block = risk >= OUTPUT_BLOCK_THRESHOLD
    should_redact = OUTPUT_REDACT_THRESHOLD <= risk < OUTPUT_BLOCK_THRESHOLD

    safe_output = output
    if should_redact:
        for pattern in SECRET_PATTERNS + PII_PATTERNS:
            try:
                safe_output = re.sub(pattern, "[REDACTED]", safe_output, flags=re.IGNORECASE)
            except re.error:
                safe_output = safe_output.replace(pattern, "[REDACTED]")

    return {
        "blocked": should_block,
        "redacted": should_redact,
        "risk": risk,
        "severity": severity,
        "reasons": reasons,
        "safe_output": safe_output,
    }


def get_policy_status() -> Dict[str, Any]:
    return {
        "prompt_injection_detection": "enabled",
        "secret_leak_detection": "enabled",
        "pii_detection": "enabled",
        "tool_policy_enforcement": "enabled",
        "blocked_tools": sorted(BLOCKED_TOOLS),
        "high_risk_tools": sorted(HIGH_RISK_TOOLS),
        "risk_thresholds": {
            "block": BLOCK_THRESHOLD,
            "critical": CRITICAL_THRESHOLD,
            "output_block": OUTPUT_BLOCK_THRESHOLD,
            "output_redact": OUTPUT_REDACT_THRESHOLD,
        },
        "roles": ROLE_POLICIES,
    }