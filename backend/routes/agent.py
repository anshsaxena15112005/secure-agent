from fastapi import APIRouter, Depends, HTTPException
from backend.models import schemas
from backend.security import auth
from backend.app.agent.executor import execute_plan

router = APIRouter()


@router.post("/run", response_model=schemas.AgentRunResponse)
async def run_agent(
    request: schemas.AgentRunRequest,
    current_user=Depends(auth.get_current_user)
):
    try:
        result = execute_plan(
            prompt=request.prompt,
            model_name=request.model_name or "gpt-4o-mini",
            username=current_user.username,
            tool=request.tool_name or "none"
        )

        status_value = result.get("status", "error")
        blocked = status_value == "blocked"

        response_text = ""
        if status_value == "ok":
            response_text = result.get("output", "")
        elif status_value == "blocked":
            response_text = ""
        elif status_value == "error":
            response_text = ""
        else:
            response_text = result.get("output", "")

        return schemas.AgentRunResponse(
            status=status_value,
            prompt=request.prompt,
            response=response_text,
            blocked=blocked,
            risk_score=result.get("risk", 0),
            reason=result.get("reason"),
            model_name=result.get("model_name", request.model_name),
            tool_name=result.get("tool", request.tool_name),
            incident_id=result.get("incident_id"),
            metadata={
                "stage": result.get("stage"),
                "severity": result.get("severity"),
                "event_id": result.get("event_id"),
                "matches": result.get("matches", []),
                "message": result.get("message"),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )