from backend.app.security import analyze_prompt, evaluate_tool_use, inspect_output
from backend.app.policy_loader import get_policy
from backend.app.db import SessionLocal, SecurityEvent, Incident


def log_event(
    app_id: str,
    role: str,
    event_type: str,
    severity: str,
    tool: str,
    reason: str,
    risk: int,
    goal: str,
):
    policy = get_policy()
    incident_threshold = policy.get("risk_thresholds", {}).get("incident", 60)

    db = SessionLocal()
    try:
        event = SecurityEvent(
            app_id=app_id,
            role=role,
            event_type=event_type,
            severity=severity,
            tool=tool,
            reason=reason,
            risk=risk,
            goal=goal,
        )
        db.add(event)
        db.commit()

        if risk >= incident_threshold:
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


def execute_plan(plan, app_id="default-app", role="user"):
    goal = plan.get("goal", "")
    tool = plan.get("tool", "none")

    prompt_check = analyze_prompt(goal)
    if prompt_check["blocked"]:
        reason = "; ".join(prompt_check["reasons"]) or "Prompt blocked by security policy"
        log_event(
            app_id=app_id,
            role=role,
            event_type="PROMPT_BLOCKED",
            severity=prompt_check["severity"],
            tool=tool,
            reason=reason,
            risk=prompt_check["risk"],
            goal=goal,
        )
        return {
            "status": "blocked",
            "stage": "prompt",
            "risk": prompt_check["risk"],
            "severity": prompt_check["severity"],
            "reason": reason,
            "matches": prompt_check["matches"],
        }

    tool_check = evaluate_tool_use(tool, role=role)
    if not tool_check["allowed"]:
        log_event(
            app_id=app_id,
            role=role,
            event_type="TOOL_BLOCKED",
            severity=tool_check["severity"],
            tool=tool,
            reason=tool_check["reason"],
            risk=tool_check["risk"],
            goal=goal,
        )
        return {
            "status": "blocked",
            "stage": "tool",
            "risk": tool_check["risk"],
            "severity": tool_check["severity"],
            "reason": tool_check["reason"],
            "tool": tool,
        }

    simulated_output = f"Executed goal safely: {goal}"

    output_check = inspect_output(simulated_output)
    if output_check["blocked"]:
        log_event(
            app_id=app_id,
            role=role,
            event_type="OUTPUT_BLOCKED",
            severity=output_check["severity"],
            tool=tool,
            reason="; ".join(output_check["reasons"]) or "Output blocked by policy",
            risk=output_check["risk"],
            goal=goal,
        )
        return {
            "status": "blocked",
            "stage": "output",
            "risk": output_check["risk"],
            "severity": output_check["severity"],
            "reason": "; ".join(output_check["reasons"]) or "Output blocked by policy",
        }

    if output_check["redacted"]:
        log_event(
            app_id=app_id,
            role=role,
            event_type="OUTPUT_REDACTED",
            severity=output_check["severity"],
            tool=tool,
            reason="; ".join(output_check["reasons"]) or "Output redacted by policy",
            risk=output_check["risk"],
            goal=goal,
        )
        return {
            "status": "ok",
            "stage": "output",
            "risk": output_check["risk"],
            "severity": output_check["severity"],
            "message": "Output redacted for safety",
            "tool": tool,
            "output": output_check["safe_output"],
        }

    combined_risk = max(prompt_check["risk"], tool_check["risk"])
    if combined_risk >= 80:
        combined_severity = "critical"
    elif combined_risk >= 60:
        combined_severity = "high"
    elif combined_risk >= 30:
        combined_severity = "medium"
    else:
        combined_severity = "low"

    log_event(
        app_id=app_id,
        role=role,
        event_type="TOOL_OK",
        severity=combined_severity,
        tool=tool,
        reason=tool_check["reason"],
        risk=combined_risk,
        goal=goal,
    )

    return {
        "status": "ok",
        "stage": "complete",
        "risk": combined_risk,
        "severity": combined_severity,
        "tool": tool,
        "output": simulated_output,
    }