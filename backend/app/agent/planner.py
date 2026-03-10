def plan_task(goal: str):
    """
    Phase 2 planner:
    Converts a user goal into a structured execution plan.
    """

    cleaned_goal = goal.strip()
    lowered_goal = cleaned_goal.lower()

    # Default plan structure
    plan = {
        "goal": cleaned_goal,
        "intent": "unknown",
        "tool": None,
        "tool_input": cleaned_goal,
        "steps": []
    }

    # Intent: calculation
    if "calculate" in lowered_goal or any(op in cleaned_goal for op in ["+", "-", "*", "/"]):
        expression = cleaned_goal.replace("calculate", "").strip()

        plan["intent"] = "calculation"
        plan["tool"] = "calculator"
        plan["tool_input"] = expression
        plan["steps"] = [
            "identify calculation request",
            "select calculator tool",
            "execute calculation"
        ]
        return plan

    # Intent: note storage
    if "note" in lowered_goal or "remember" in lowered_goal or "save" in lowered_goal:
        plan["intent"] = "note_storage"
        plan["tool"] = "notes_store"
        plan["tool_input"] = cleaned_goal
        plan["steps"] = [
            "identify note storage request",
            "select notes_store tool",
            "store note"
        ]
        return plan

    # Fallback
    plan["intent"] = "default"
    plan["tool"] = "notes_store"
    plan["tool_input"] = cleaned_goal
    plan["steps"] = [
        "could not classify intent clearly",
        "fallback to notes_store tool"
    ]

    return plan