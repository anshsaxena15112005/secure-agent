from typing import Dict


def plan(goal: str) -> Dict:
    """
    Decide which tool should be used based on the user goal.
    Returns a simple execution plan.
    """

    goal = goal.strip()

    # simple heuristic planner for now
    if any(ch.isdigit() for ch in goal) and any(op in goal for op in "+-*/"):
        tool = "calculator"
    else:
        tool = "notes_store"

    return {
        "goal": goal,
        "tool": tool
    }