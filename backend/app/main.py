from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.db import init_db
from backend.app.agent.planner import plan_task
from backend.app.agent.executor import execute_tool
from backend.app.security import allow_tool_call

app = FastAPI()

init_db()


class AgentRequest(BaseModel):
    goal: str


@app.get("/")
def root():
    return {"message": "Secure Agent Running"}


@app.post("/agent/run")
def run_agent(request: AgentRequest):

    goal = request.goal

    # planner decides tool
    tool_name, tool_input = plan_task(goal)

    # security layer
    allowed, reason, risk = allow_tool_call(goal, tool_name)

    if not allowed:
        return {
            "status": "blocked",
            "reason": reason,
            "risk": risk
        }

    # executor runs tool
    result = execute_tool(tool_name, tool_input)

    return {
        "status": "ok",
        "tool": tool_name,
        "output": result
    }