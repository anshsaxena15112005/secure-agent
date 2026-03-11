from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.db import init_db, SessionLocal, SecurityEvent
from backend.app.agent.planner import plan_task
from backend.app.agent.executor import execute_plan

app = FastAPI(
    title="SecureAgent",
    description="Backend-first AI agent with runtime security",
    version="2.1"
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
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
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


@app.get("/security/stats")
def security_stats():
    db = SessionLocal()
    try:
        rows = db.query(SecurityEvent).all()

        total_events = len(rows)
        blocked_events = sum(1 for r in rows if r.event_type in {"PROMPT_BLOCKED", "TOOL_BLOCKED"})
        allowed_events = sum(1 for r in rows if r.event_type == "TOOL_OK")
        high_risk_events = sum(1 for r in rows if (r.risk or 0) >= 60)

        by_tool = {}
        for r in rows:
            tool = r.tool or "unknown"
            by_tool[tool] = by_tool.get(tool, 0) + 1

        by_event_type = {}
        for r in rows:
            event_type = r.event_type or "unknown"
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1

        return {
            "total_events": total_events,
            "blocked_events": blocked_events,
            "allowed_events": allowed_events,
            "high_risk_events": high_risk_events,
            "by_tool": by_tool,
            "by_event_type": by_event_type,
        }
    finally:
        db.close()