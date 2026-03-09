from typing import Dict

from app.security import allow_tool_call, log_event
from app.tools import TOOLS


def execute(plan: Dict) -> Dict:
    goal = plan["goal"]
    tool_name = plan["tool"]

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

    # TOOL REGISTRY LOOKUP
    tool = TOOLS.get(tool_name)

    if not tool:
        return {
            "status": "error",
            "reason": "Tool not found"
        }

    output = tool(goal)

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