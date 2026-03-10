from backend.app.tools import calculator, notes_store


def execute_tool(tool_name, tool_input):

    if tool_name == "calculator":
        return calculator(tool_input)

    if tool_name == "notes_store":
        return notes_store(tool_input)

    return "unknown tool"