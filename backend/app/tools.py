import math

def calculator(expression: str) -> str:
    """
    Safely evaluate a simple math expression.
    Only digits and math operators are allowed.
    """
    allowed = set("0123456789+-*/(). %")

    # Block unsafe characters
    if any(ch not in allowed for ch in expression):
        return "Blocked: invalid characters"

    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def notes_store(text: str) -> str:
    """
    Dummy storage tool for Phase 1.
    Later this can store notes in a database.
    """
    return f"Note saved: {text}"