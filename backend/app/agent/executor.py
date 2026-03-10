from ..tools import TOOLS # Ensure this matches tools.py
from ..security import log_event

def execute_tool(tool_name, tool_input, goal):
    tool_func = TOOLS.get(tool_name)
    
    if not tool_func:
        return "Error: Unknown tool"

    try:
        output = tool_func(tool_input)
        # Log success to DB
        log_event("TOOL_OK", goal, tool_name, "Executed successfully", 0)
        return output
    except Exception as e:
        return f"Execution Error: {str(e)}"