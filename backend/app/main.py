from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.db import init_db, SessionLocal, SecurityEvent
from backend.app.agent.planner import plan_task
from backend.app.agent.executor import execute_plan

app = FastAPI(
    title="SecureAgent",
    description="Backend-first AI agent with runtime security",
    version="2.0"
)

init_db()


class AgentRequest(BaseModel):
    goal: str


@app.get("/")
def root():
    return {"message": "Secure Agent Running"}


@app.post("/agent/run")
def run_agent(request: AgentRequest):
    plan = plan_task(request.goal)
    result = execute_plan(plan)
    return result


@app.get("/events")
def get_events(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.query(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(limit).all()

        return [
            {
                "id": row.id,
                "event_type": row.event_type,
                "tool": row.tool,
                "reason": row.reason,
                "risk": row.risk,
                "goal": row.goal,
            }
            for row in rows
        ]
    finally:
        db.close()