def plan_task(goal: str):
    g = goal.lower()
    if "calculate" in g or any(op in g for op in "+-*/"):
        expression = g.replace("calculate", "").strip()
        return "calculator", expression
    
    if "note" in g:
        return "notes_store", goal
        
    return "notes_store", goal # Default fallback