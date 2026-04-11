from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc

from backend.security import auth
from backend.app.db import SessionLocal, SecurityEvent

router = APIRouter()


def _serialize_event(event: SecurityEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "app_id": event.app_id,
        "role": event.role,
        "event_type": event.event_type,
        "severity": event.severity,
        "tool": event.tool,
        "reason": event.reason,
        "risk": event.risk,
        "goal": event.goal,
    }


@router.get("")
async def get_events(current_user=Depends(auth.get_current_user), limit: int = 20):
    db = SessionLocal()
    try:
        events = (
            db.query(SecurityEvent)
            .order_by(desc(SecurityEvent.timestamp))
            .limit(limit)
            .all()
        )
        return [_serialize_event(event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")
    finally:
        db.close()