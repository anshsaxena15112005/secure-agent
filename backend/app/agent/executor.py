import asyncio
from typing import Any, Dict, Optional

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


def _normalize_plan_input(plan_or_prompt: Any) -> Dict[str, Any]:
    if isinstance(plan_or_prompt, str):
        return {
            "goal": plan_or_prompt,
            "tool": "none",
            "context": {},
        }

    if isinstance(plan_or_prompt, dict):
        return {
            "goal": (
                plan_or_prompt.get("prompt")
                or plan_or_prompt.get("goal")
                or plan_or_prompt.get("task")
                or ""
            ),
            "tool": (
                plan_or_prompt.get("tool_name")
                or plan_or_prompt.get("tool")
                or "none"
            ),
            "context": plan_or_prompt.get("context") or {},
        }

    return {
        "goal": (
            getattr(plan_or_prompt, "prompt", None)
            or getattr(plan_or_prompt, "goal", None)
            or getattr(plan_or_prompt, "task", None)
            or ""
        ),
        "tool": (
            getattr(plan_or_prompt, "tool_name", None)
            or getattr(plan_or_prompt, "tool", None)
            or "none"
        ),
        "context": getattr(plan_or_prompt, "context", None) or {},
    }


def _build_result(
    *,
    status: str,
    goal: str,
    response: str,
    blocked: bool,
    risk: int,
    severity: str,
    reason: Optional[str],
    tool: str,
    model_name: str,
    incident_id: Optional[int],
    event_id: Optional[int],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        # old test-compatible keys
        "status": status,
        "risk": risk,
        "severity": severity,
        "tool": tool,

        # new API/frontend-compatible keys
        "prompt": goal,
        "response": response,
        "blocked": blocked,
        "risk_score": risk,
        "reason": reason,
        "model_name": model_name,
        "tool_name": tool,
        "incident_id": incident_id,
        "metadata": {
            "event_id": event_id,
            **(metadata or {}),
        },
    }


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
    plan_or_prompt,
    app_id: str = "default-app",
    role: str = "user",
    model_name: str = "mock",
    username: Optional[str] = None,
) -> dict:
    normalized = _normalize_plan_input(plan_or_prompt)

    goal = normalized["goal"]
    tool = normalized["tool"] or "none"
    effective_role = role or "user"
    effective_username = username or effective_role

    prompt_check = analyze_prompt(goal)
    prompt_risk = int(prompt_check.get("risk", 0))
    prompt_severity = prompt_check.get("severity") or _risk_to_severity(prompt_risk)

    if prompt_check.get("blocked", False):
        reason = "; ".join(prompt_check.get("reasons", [])) or "Prompt blocked by security policy"
        logged = log_event(
            app_id=app_id,
            role=effective_role,
            event_type="PROMPT_BLOCKED",
            severity=prompt_severity,
            tool=tool,
            reason=reason,
            risk=prompt_risk,
            goal=goal,
        )
        return _build_result(
            status="blocked",
            goal=goal,
            response="",
            blocked=True,
            risk=prompt_risk,
            severity=prompt_severity,
            reason=reason,
            tool=tool,
            model_name=model_name,
            incident_id=logged["incident"]["id"] if logged["incident"] else None,
            event_id=logged["event"]["id"],
            metadata={
                "stage": "prompt",
                "matches": prompt_check.get("matches", {}),
                "username": effective_username,
                "role": effective_role,
                "app_id": app_id,
            },
        )

    tool_check = evaluate_tool_use(tool, role=effective_role)
    tool_allowed = tool_check.get("allowed", True)
    tool_risk = int(tool_check.get("risk", 0))
    tool_severity = tool_check.get("severity") or _risk_to_severity(tool_risk)

    if not tool_allowed:
        reason = tool_check.get("reason", "Tool blocked by policy")
        logged = log_event(
            app_id=app_id,
            role=effective_role,
            event_type="TOOL_BLOCKED",
            severity=tool_severity,
            tool=tool,
            reason=reason,
            risk=tool_risk,
            goal=goal,
        )
        return _build_result(
            status="blocked",
            goal=goal,
            response="",
            blocked=True,
            risk=tool_risk,
            severity=tool_severity,
            reason=reason,
            tool=tool,
            model_name=model_name,
            incident_id=logged["incident"]["id"] if logged["incident"] else None,
            event_id=logged["event"]["id"],
            metadata={
                "stage": "tool",
                "username": effective_username,
                "role": effective_role,
                "app_id": app_id,
            },
        )

    try:
        model_output = generate_response(prompt=goal, model=model_name)
    except Exception as e:
        reason = f"Model call failed: {str(e)}"
        logged = log_event(
            app_id=app_id,
            role=effective_role,
            event_type="MODEL_ERROR",
            severity="high",
            tool=tool,
            reason=reason,
            risk=70,
            goal=goal,
        )
        return _build_result(
            status="error",
            goal=goal,
            response="",
            blocked=False,
            risk=70,
            severity="high",
            reason=reason,
            tool=tool,
            model_name=model_name,
            incident_id=logged["incident"]["id"] if logged["incident"] else None,
            event_id=logged["event"]["id"],
            metadata={
                "stage": "model",
                "username": effective_username,
                "role": effective_role,
                "app_id": app_id,
            },
        )

    output_check = inspect_output(model_output)
    output_risk = int(output_check.get("risk", 0))
    output_severity = output_check.get("severity") or _risk_to_severity(output_risk)

    if output_check.get("blocked", False):
        reason = "; ".join(output_check.get("reasons", [])) or "Output blocked by policy"
        logged = log_event(
            app_id=app_id,
            role=effective_role,
            event_type="OUTPUT_BLOCKED",
            severity=output_severity,
            tool=tool,
            reason=reason,
            risk=output_risk,
            goal=goal,
        )
        return _build_result(
            status="blocked",
            goal=goal,
            response="",
            blocked=True,
            risk=output_risk,
            severity=output_severity,
            reason=reason,
            tool=tool,
            model_name=model_name,
            incident_id=logged["incident"]["id"] if logged["incident"] else None,
            event_id=logged["event"]["id"],
            metadata={
                "stage": "output",
                "username": effective_username,
                "role": effective_role,
                "app_id": app_id,
            },
        )

    if output_check.get("redacted", False):
        reason = "; ".join(output_check.get("reasons", [])) or "Output redacted by policy"
        safe_output = output_check.get("safe_output", "")
        logged = log_event(
            app_id=app_id,
            role=effective_role,
            event_type="OUTPUT_REDACTED",
            severity=output_severity,
            tool=tool,
            reason=reason,
            risk=output_risk,
            goal=goal,
        )
        return _build_result(
            status="ok",
            goal=goal,
            response=safe_output,
            blocked=False,
            risk=output_risk,
            severity=output_severity,
            reason=reason,
            tool=tool,
            model_name=model_name,
            incident_id=logged["incident"]["id"] if logged["incident"] else None,
            event_id=logged["event"]["id"],
            metadata={
                "stage": "output",
                "message": "Output redacted for safety",
                "username": effective_username,
                "role": effective_role,
                "app_id": app_id,
            },
        )

    combined_risk = max(prompt_risk, tool_risk, output_risk)
    combined_severity = _risk_to_severity(combined_risk)

    logged = log_event(
        app_id=app_id,
        role=effective_role,
        event_type="REQUEST_COMPLETED",
        severity=combined_severity,
        tool=tool,
        reason="Request completed successfully",
        risk=combined_risk,
        goal=goal,
    )

    return _build_result(
        status="ok",
        goal=goal,
        response=model_output,
        blocked=False,
        risk=combined_risk,
        severity=combined_severity,
        reason="Request completed successfully",
        tool=tool,
        model_name=model_name,
        incident_id=logged["incident"]["id"] if logged["incident"] else None,
        event_id=logged["event"]["id"],
        metadata={
            "stage": "complete",
            "username": effective_username,
            "role": effective_role,
            "app_id": app_id,
        },
    )