from typing import Dict

from app.security import allow_tool_call, log_event
from app.tools import calculator, notes_store


def execute(plan: Dict) -> Dict:
    """
    Execute a planned tool call safely.
    """
    goal = plan["goal"]
    tool_name = plan["tool"]

    # 1) Security check before execution
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
            "tool": tool_name,
            "reason": reason,
            "risk": risk
        }

    # 2) Execute allowed tool
    if tool_name == "calculator":
        output = calculator(goal)
    elif tool_name == "notes_store":
        output = notes_store(goal)
    else:
        # fallback safety
        log_event(
            event_type="TOOL_BLOCKED",
            goal=goal,
            tool=tool_name,
            reason="Unknown tool requested",
            risk=80
        )
        return {
            "status": "blocked",
            "tool": tool_name,
            "reason": "Unknown tool requested",
            "risk": 80
        }

    # 3) Log successful execution
    log_event(
        event_type="TOOL_OK",
        goal=goal,
        tool=tool_name,
        reason="Executed successfully",
        risk=0
    )

    return {
        "status": "ok",
        "tool": tool_name,
        "output": output
    }