from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc

from backend.security import auth
from backend.app.db import SessionLocal, Incident

router = APIRouter()


def _serialize_incident(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "severity": incident.severity,
        "category": incident.event_type,
        "message": incident.reason,
        "blocked": True,
        "timestamp": incident.timestamp.isoformat() if incident.timestamp else None,
        "source": incident.app_id,
        "tool": incident.tool,
        "risk": incident.risk,
        "role": incident.role,
        "status": incident.status,
        "goal": incident.goal,
    }


@router.get("")
async def list_incidents(current_user=Depends(auth.get_current_user), limit: int = 20):
    db = SessionLocal()
    try:
        incidents = (
            db.query(Incident)
            .order_by(desc(Incident.timestamp))
            .limit(limit)
            .all()
        )
        return [_serialize_incident(incident) for incident in incidents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")
    finally:
        db.close()


@router.get("/{incident_id}")
async def get_incident(incident_id: int, current_user=Depends(auth.get_current_user)):
    db = SessionLocal()
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()

        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        return _serialize_incident(incident)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incident: {str(e)}")
    finally:
        db.close()