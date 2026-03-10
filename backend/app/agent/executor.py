from backend.app.tools import TOOLS
from backend.app.security import allow_tool_call, log_event


def execute_plan(plan: dict):
    """
    Phase 2 executor:
    - reads structured plan
    - checks security
    - finds tool from registry
    - executes tool
    - logs result
    """

    goal = plan["goal"]
    tool_name = plan["tool"]
    tool_input = plan["tool_input"]

    # 1. Security check before execution
    allowed, reason, risk = allow_tool_call(goal, tool_name)

    if not allowed:
        log_event(
            event_type="PROMPT_BLOCKED",
            goal=goal,
            tool=tool_name,
            reason=reason,
            risk=risk
        )
        return {
            "status": "blocked",
            "goal": goal,
            "tool": tool_name,
            "reason": reason,
            "risk": risk,
            "steps": plan.get("steps", [])
        }

    # 2. Tool lookup from registry
    tool_func = TOOLS.get(tool_name)

    if tool_func is None:
        log_event(
            event_type="TOOL_BLOCKED",
            goal=goal,
            tool=tool_name,
            reason="Unknown tool requested",
            risk=80
        )
        return {
            "status": "error",
            "goal": goal,
            "tool": tool_name,
            "reason": "Unknown tool requested",
            "risk": 80,
            "steps": plan.get("steps", [])
        }

    # 3. Execute tool
    output = tool_func(tool_input)

    # 4. Log success
    log_event(
        event_type="TOOL_OK",
        goal=goal,
        tool=tool_name,
        reason="Executed successfully",
        risk=0
    )

    return {
        "status": "ok",
        "goal": goal,
        "intent": plan.get("intent"),
        "tool": tool_name,
        "tool_input": tool_input,
        "steps": plan.get("steps", []),
        "output": output
    }