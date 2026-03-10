from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent import planner, executor
from .security import allow_tool_call, log_event
from .db import init_db

app = FastAPI(title="SecureAgent")

# Create database on start
init_db()

class AgentRequest(BaseModel):
    goal: str

@app.get("/")
def root():
    return {"message": "Secure AI Agent Running", "docs": "/docs"}

@app.post("/agent/run")
def run_agent(request: AgentRequest):
    goal = request.goal

    # 1. Plan
    tool_name, tool_input = planner.plan_task(goal)

    # 2. Security Check
    allowed, reason, risk = allow_tool_call(goal, tool_name)

    if not allowed:
        log_event("PROMPT_BLOCKED", goal, tool_name, reason, risk)
        return {"status": "blocked", "reason": reason, "risk_score": risk}

    # 3. Execute
    result = executor.execute_tool(tool_name, tool_input, goal)
    return {"status": "ok", "output": result}