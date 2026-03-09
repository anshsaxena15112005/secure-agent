def calculator(expression: str):
    try:
        return eval(expression)
    except Exception:
        return "Invalid expression"


notes = []


def notes_store(text: str):
    notes.append(text)
    return {"stored": text}


# TOOL REGISTRY
TOOLS = {
    "calculator": calculator,
    "notes_store": notes_store,
}