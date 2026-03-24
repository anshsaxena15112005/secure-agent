def plan_task(goal: str):
    cleaned_goal = goal.strip()
    lowered_goal = cleaned_goal.lower()

    plan = {
        "goal": cleaned_goal,
        "intent": "unknown",
        "tool": None,
        "tool_input": cleaned_goal,
        "steps": []
    }

    if "demo leak" in lowered_goal:
        plan["intent"] = "output_security_test"
        plan["tool"] = "demo_leak"
        plan["tool_input"] = cleaned_goal
        plan["steps"] = [
            "identify output security test request",
            "select demo_leak tool",
            "execute output inspection workflow"
        ]
        return plan

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

    plan["intent"] = "default"
    plan["tool"] = "notes_store"
    plan["tool_input"] = cleaned_goal
    plan["steps"] = [
        "could not classify intent clearly",
        "fallback to notes_store tool"
    ]

    return plan