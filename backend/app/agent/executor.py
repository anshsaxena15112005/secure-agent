from backend.app.tools import TOOLS
from backend.app.security import allow_tool_call, log_event


def execute_plan(plan: dict, app_id: str = "default-app", role: str = "user"):
    goal = plan["goal"]
    tool_name = plan["tool"]
    tool_input = plan["tool_input"]

    allowed, reason, risk = allow_tool_call(goal, tool_name, role=role)

    if not allowed:
        log_event(
            event_type="PROMPT_BLOCKED",
            goal=goal,
            tool=tool_name,
            reason=reason,
            risk=risk,
            app_id=app_id,
            role=role
        )
        return {
            "status": "blocked",
            "app_id": app_id,
            "role": role,
            "goal": goal,
            "tool": tool_name,
            "reason": reason,
            "risk": risk,
            "severity": "critical" if risk >= 85 else "high" if risk >= 60 else "medium",
            "steps": plan.get("steps", [])
        }

    tool_func = TOOLS.get(tool_name)

    if tool_func is None:
        log_event(
            event_type="TOOL_BLOCKED",
            goal=goal,
            tool=tool_name,
            reason="Unknown tool requested",
            risk=80,
            app_id=app_id,
            role=role
        )
        return {
            "status": "error",
            "app_id": app_id,
            "role": role,
            "goal": goal,
            "tool": tool_name,
            "reason": "Unknown tool requested",
            "risk": 80,
            "severity": "high",
            "steps": plan.get("steps", [])
        }

    output = tool_func(tool_input)

    log_event(
        event_type="TOOL_OK",
        goal=goal,
        tool=tool_name,
        reason="Executed successfully",
        risk=0,
        app_id=app_id,
        role=role
    )

    return {
        "status": "ok",
        "app_id": app_id,
        "role": role,
        "goal": goal,
        "intent": plan.get("intent"),
        "tool": tool_name,
        "tool_input": tool_input,
        "steps": plan.get("steps", []),
        "severity": "low",
        "output": output
    }