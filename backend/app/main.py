from fastapi import FastAPI
from pydantic import BaseModel

from app.db import init_db, SessionLocal, SecurityEvent
from app.agent.planner import plan
from app.agent.executor import execute

app = FastAPI(title="SecureAgent Backend")

# Initialize database
init_db()


class RunRequest(BaseModel):
    goal: str


@app.get("/")
def home():
    return {"message": "SecureAgent backend is running"}


@app.post("/run")
def run(req: RunRequest):
    execution_plan = plan(req.goal)
    result = execute(execution_plan)
    return result


@app.get("/events")
def get_events(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.query(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(limit).all()

        return [
            {
                "id": row.id,
                "timestamp": str(row.timestamp),
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