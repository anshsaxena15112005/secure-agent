from fastapi import FastAPI
from pydantic import BaseModel

from app.db import init_db, SessionLocal, SecurityEvent
from app.security import allow_tool_call, log_event
from app.tools import calculator, notes_store

app = FastAPI(title="SecureAgent Backend")

# Create database tables on startup
init_db()


class RunRequest(BaseModel):
    goal: str


@app.get("/")
def home():
    return {"message": "SecureAgent backend is running"}


@app.post("/run")
def run(req: RunRequest):
    goal = req.goal.strip()

    # Very simple planner for Phase 1:
    # if the input looks like a math expression, use calculator
    # otherwise use notes_store
    if any(ch.isdigit() for ch in goal) and any(op in goal for op in "+-*/"):
        tool_name = "calculator"

        allowed, reason, risk = allow_tool_call(goal, tool_name)
        if not allowed:
            log_event("PROMPT_BLOCKED", goal, tool=tool_name, reason=reason, risk=risk)
            return {
                "status": "blocked",
                "tool": tool_name,
                "reason": reason,
                "risk": risk
            }

        output = calculator(goal)
        log_event("TOOL_OK", goal, tool=tool_name, reason="Executed successfully", risk=0)

        return {
            "status": "ok",
            "tool": tool_name,
            "output": output
        }

    # Default tool
    tool_name = "notes_store"

    allowed, reason, risk = allow_tool_call(goal, tool_name)
    if not allowed:
        log_event("PROMPT_BLOCKED", goal, tool=tool_name, reason=reason, risk=risk)
        return {
            "status": "blocked",
            "tool": tool_name,
            "reason": reason,
            "risk": risk
        }

    output = notes_store(goal)
    log_event("TOOL_OK", goal, tool=tool_name, reason="Executed successfully", risk=0)

    return {
        "status": "ok",
        "tool": tool_name,
        "output": output
    }


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