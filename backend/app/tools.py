notes_memory = []


def calculator(expression: str):
    """
    Simple calculator tool.
    Evaluates basic math expressions.
    """
    try:
        return eval(expression)
    except Exception:
        return "invalid expression"


def notes_store(text: str):
    """
    Simple note storage tool.
    Stores notes in memory for now.
    """
    notes_memory.append(text)
    return "note stored"


TOOLS = {
    "calculator": calculator,
    "notes_store": notes_store,
}