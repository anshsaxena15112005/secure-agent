import re
from typing import Dict, Any, List


PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|previous|prior) instructions",
    r"reveal (the )?(system prompt|hidden prompt|developer message)",
    r"developer message",
    r"system prompt",
    r"bypass security",
    r"disable safety",
    r"forget previous instructions",
    r"override rules",
    r"jailbreak",
    r"dump password",
    r"show me the api key",
    r"leak (credentials|secrets|tokens|passwords)",
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"api[_\- ]?key",
    r"access[_\- ]?token",
    r"secret[_\- ]?key",
    r"password",
    r"private[_\- ]?key",
    r"bearer\s+[A-Za-z0-9\-_\.]+",
]

PII_PATTERNS = [
    r"\b\d{10}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    r"\b\d{12}\b",
]

BLOCKED_TOOLS = {"shell", "terminal", "filesystem_delete", "db_admin"}
HIGH_RISK_TOOLS = {"webhook", "filesystem_write", "external_api", "email_send"}


def _match_patterns(text: str, patterns: List[str]) -> List[str]:
    matches = []
    lower_text = text.lower()

    for pattern in patterns:
        if re.search(pattern, lower_text, flags=re.IGNORECASE):
            matches.append(pattern)

    return matches


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

    severity = "low"
    if risk >= 80:
        severity = "critical"
    elif risk >= 60:
        severity = "high"
    elif risk >= 30:
        severity = "medium"

    blocked = risk >= 60

    return {
        "blocked": blocked,
        "risk": min(risk, 100),
        "severity": severity,
        "reasons": reasons,
        "matches": {
            "prompt_injection": matched_injection,
            "secrets": matched_secrets,
            "pii": matched_pii,
        },
    }


def evaluate_tool_use(tool_name: str) -> Dict[str, Any]:
    tool = (tool_name or "").strip().lower()

    if tool in BLOCKED_TOOLS:
        return {
            "allowed": False,
            "risk": 90,
            "severity": "critical",
            "reason": f"Tool '{tool}' is blocked by policy",
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
    redactions = []

    if matched_secrets:
        risk += 50
        reasons.append("Sensitive secret-like content detected in output")
        redactions.extend(matched_secrets)

    if matched_pii:
        risk += 25
        reasons.append("Possible PII detected in output")
        redactions.extend(matched_pii)

    severity = "low"
    if risk >= 70:
        severity = "high"
    elif risk >= 30:
        severity = "medium"

    should_block = risk >= 70
    should_redact = 30 <= risk < 70

    safe_output = output
    if should_redact:
        for pattern in SECRET_PATTERNS + PII_PATTERNS:
            safe_output = re.sub(pattern, "[REDACTED]", safe_output, flags=re.IGNORECASE)

    return {
        "blocked": should_block,
        "redacted": should_redact,
        "risk": min(risk, 100),
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
    }