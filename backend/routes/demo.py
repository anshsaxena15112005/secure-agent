from fastapi import APIRouter, Depends
from backend.security import auth

router = APIRouter()

fake_events = []
fake_incidents = []

@router.post("/seed")
async def seed_demo(current_user=Depends(auth.get_current_user)):
    global fake_events, fake_incidents

    fake_events = [
        {"event_type": "PROMPT_BLOCKED", "severity": "high", "risk": 75, "reason": "Prompt injection"},
        {"event_type": "TOOL_ALLOWED", "severity": "low", "risk": 10, "reason": "Safe usage"}
    ]

    fake_incidents = [
        {"event_type": "SECURITY_ALERT", "severity": "high", "risk": 80, "reason": "Secret leak attempt"}
    ]

    return {
        "seeded_events": len(fake_events),
        "seeded_incidents": len(fake_incidents)
    }


@router.post("/clear")
async def clear_demo(current_user=Depends(auth.get_current_user)):
    global fake_events, fake_incidents

    count_events = len(fake_events)
    count_incidents = len(fake_incidents)

    fake_events = []
    fake_incidents = []

    return {
        "deleted_events": count_events,
        "deleted_incidents": count_incidents
    }