from fastapi import APIRouter, Depends, HTTPException

from backend.security import auth
from backend.app.db import SessionLocal, SecurityEvent, Incident

router = APIRouter()


@router.get("/summary")
async def get_report_summary(current_user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        events = db.query(SecurityEvent).all()
        incidents = db.query(Incident).all()

        total_requests = len(events)
        blocked_requests = len(
            [
                event for event in events
                if "BLOCKED" in str(event.event_type or "")
            ]
        )
        allowed_requests = max(total_requests - blocked_requests, 0)
        total_incidents = len(incidents)
        high_risk_count = len(
            [
                event for event in events
                if (event.risk or 0) >= 60
            ]
        )

        return {
            "total_requests": total_requests,
            "blocked_requests": blocked_requests,
            "allowed_requests": allowed_requests,
            "total_incidents": total_incidents,
            "high_risk_count": high_risk_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report summary: {str(e)}")
    finally:
        db.close()