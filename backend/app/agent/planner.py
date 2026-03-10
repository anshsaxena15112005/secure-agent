def plan_task(goal: str):

    g = goal.lower()

    if "calculate" in g:
        expr = g.replace("calculate", "").strip()
        return "calculator", expr

    if "note" in g:
        return "notes_store", goal

    return "calculator", goal