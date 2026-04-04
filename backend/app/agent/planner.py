def plan_task(goal: str):
    text = (goal or "").lower()

    tool = "none"
    if any(word in text for word in ["email", "send mail", "mail"]):
        tool = "email_send"
    elif any(word in text for word in ["api", "request", "fetch", "http"]):
        tool = "external_api"
    elif any(word in text for word in ["write file", "save file", "create file"]):
        tool = "filesystem_write"
    elif any(word in text for word in ["delete file", "remove file", "wipe"]):
        tool = "filesystem_delete"
    elif any(word in text for word in ["run shell", "terminal", "command line", "bash", "shell"]):
        tool = "shell"
    elif any(word in text for word in ["webhook", "callback url"]):
        tool = "webhook"

    return {
        "goal": goal,
        "tool": tool,
    }