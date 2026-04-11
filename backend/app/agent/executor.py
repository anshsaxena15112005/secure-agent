import asyncio
from typing import Optional

from backend.app.security import analyze_prompt, evaluate_tool_use, inspect_output
from backend.app.policy_loader import get_policy
from backend.app.db import SessionLocal, SecurityEvent, Incident
from backend.app.ws_manager import manager
from backend.app.providers.openai_provider import generate_response


def _serialize_event(event: SecurityEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "app_id": event.app_id,
        "role": event.role,
        "event_type": event.event_type,
        "severity": event.severity,
        "tool": event.tool,
        "reason": event.reason,
        "risk": event.risk,
        "goal": event.goal,
    }


def _serialize_incident(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "timestamp": incident.timestamp.isoformat() if incident.timestamp else None,
        "app_id": incident.app_id,
        "role": incident.role,
        "event_type": incident.event_type,
        "severity": incident.severity,
        "tool": incident.tool,
        "reason": incident.reason,
        "risk": incident.risk,
        "goal": incident.goal,
        "status": incident.status,
    }


def _broadcast_payload(payload: dict) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(payload))
    except RuntimeError:
        pass


def _risk_to_severity(risk: int) -> str:
    if risk >= 80:
        return "critical"
    if risk >= 60:
        return "high"
    if risk >= 30:
        return "medium"
    return "low"


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
        db.refresh(event)

        _broadcast_payload(
            {
                "type": "security_event",
                "event": _serialize_event(event),
            }
        )

        created_incident = None

        if risk >= incident_threshold:
            created_incident = Incident(
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
            db.add(created_incident)
            db.commit()
            db.refresh(created_incident)

            _broadcast_payload(
                {
                    "type": "incident_created",
                    "incident": _serialize_incident(created_incident),
                }
            )

        return {
            "event": _serialize_event(event),
            "incident": _serialize_incident(created_incident) if created_incident else None,
        }

    finally:
        db.close()


def execute_plan(
    prompt: str,
    model_name: str = "gpt-4o-mini",
    username: str = "user",
    app_id: str = "default-app",
    tool: str = "none",
) -> dict:
    goal = prompt
    role = username

    prompt_check = analyze_prompt(goal)
    if prompt_check["blocked"]:
        reason = "; ".join(prompt_check.get("reasons", [])) or "Prompt blocked by security policy"
        logged = log_event(
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
            "matches": prompt_check.get("matches", []),
            "tool": tool,
            "model_name": model_name,
            "event_id": logged["event"]["id"],
            "incident_id": logged["incident"]["id"] if logged["incident"] else None,
        }

    tool_check = evaluate_tool_use(tool, role=role)
    if not tool_check["allowed"]:
        logged = log_event(
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
            "model_name": model_name,
            "event_id": logged["event"]["id"],
            "incident_id": logged["incident"]["id"] if logged["incident"] else None,
        }

    try:
        model_output = generate_response(prompt=goal, model=model_name)
    except Exception as e:
        logged = log_event(
            app_id=app_id,
            role=role,
            event_type="MODEL_ERROR",
            severity="high",
            tool=tool,
            reason=f"Model call failed: {str(e)}",
            risk=70,
            goal=goal,
        )
        return {
            "status": "error",
            "stage": "model",
            "risk": 70,
            "severity": "high",
            "reason": f"Model call failed: {str(e)}",
            "tool": tool,
            "model_name": model_name,
            "event_id": logged["event"]["id"],
            "incident_id": logged["incident"]["id"] if logged["incident"] else None,
        }

    output_check = inspect_output(model_output)
    if output_check["blocked"]:
        reason = "; ".join(output_check.get("reasons", [])) or "Output blocked by policy"
        logged = log_event(
            app_id=app_id,
            role=role,
            event_type="OUTPUT_BLOCKED",
            severity=output_check["severity"],
            tool=tool,
            reason=reason,
            risk=output_check["risk"],
            goal=goal,
        )
        return {
            "status": "blocked",
            "stage": "output",
            "risk": output_check["risk"],
            "severity": output_check["severity"],
            "reason": reason,
            "tool": tool,
            "model_name": model_name,
            "event_id": logged["event"]["id"],
            "incident_id": logged["incident"]["id"] if logged["incident"] else None,
        }

    if output_check["redacted"]:
        reason = "; ".join(output_check.get("reasons", [])) or "Output redacted by policy"
        logged = log_event(
            app_id=app_id,
            role=role,
            event_type="OUTPUT_REDACTED",
            severity=output_check["severity"],
            tool=tool,
            reason=reason,
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
            "model_name": model_name,
            "output": output_check["safe_output"],
            "event_id": logged["event"]["id"],
            "incident_id": logged["incident"]["id"] if logged["incident"] else None,
        }

    combined_risk = max(
        prompt_check.get("risk", 0),
        tool_check.get("risk", 0),
        output_check.get("risk", 0),
    )
    combined_severity = _risk_to_severity(combined_risk)

    logged = log_event(
        app_id=app_id,
        role=role,
        event_type="REQUEST_COMPLETED",
        severity=combined_severity,
        tool=tool,
        reason="Request completed successfully",
        risk=combined_risk,
        goal=goal,
    )

    return {
        "status": "ok",
        "stage": "complete",
        "risk": combined_risk,
        "severity": combined_severity,
        "reason": "Request completed successfully",
        "tool": tool,
        "model_name": model_name,
        "output": model_output,
        "event_id": logged["event"]["id"],
        "incident_id": logged["incident"]["id"] if logged["incident"] else None,
    }