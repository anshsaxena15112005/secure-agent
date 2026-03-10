notes_memory = []


def calculator(expression: str):

    try:
        result = eval(expression)
        return result
    except:
        return "invalid expression"


def notes_store(text: str):

    notes_memory.append(text)

    return "note stored"