from pathlib import Path
from datetime import datetime
import shutil

from fastapi import APIRouter, Depends, HTTPException
import yaml

from backend.models import schemas
from backend.security import auth

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_DIR = BASE_DIR / "policies"
POLICY_PATH = POLICY_DIR / "default_policy.yaml"
BACKUP_DIR = POLICY_DIR / "history"
DEFAULT_BACKUP_PATH = POLICY_DIR / "default_policy.backup.yaml"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def read_policy_text() -> str:
    if not POLICY_PATH.exists():
        raise FileNotFoundError("Policy file not found")
    return POLICY_PATH.read_text(encoding="utf-8")


def write_policy_text(content: str) -> None:
    POLICY_PATH.write_text(content, encoding="utf-8")


def validate_yaml(content: str):
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")


def create_backup() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"policy_{timestamp}.yaml"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(POLICY_PATH, backup_path)
    return backup_name


def require_admin(current_user):
    if getattr(current_user, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/evaluate", response_model=schemas.PolicyEvaluationResponse)
async def evaluate_policy(
    request: schemas.PolicyEvaluationRequest,
    current_user=Depends(auth.get_current_user)
):
    try:
        with open(POLICY_PATH, "r", encoding="utf-8") as file:
            policy = yaml.safe_load(file)

        allowed_actions = policy.get("default_role", {}).get("allowed_actions", [])

        if request.action in allowed_actions:
            return schemas.PolicyEvaluationResponse(
                allowed=True,
                reason="Matched allowed action in default policy"
            )

        return schemas.PolicyEvaluationResponse(
            allowed=False,
            reason="Action not permitted by policy"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate policy: {str(e)}"
        )


@router.get("/raw")
async def get_raw_policy(current_user=Depends(auth.get_current_user)):
    require_admin(current_user)
    try:
        return {
            "content": read_policy_text()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy: {str(e)}")


@router.post("/update")
async def update_policy(payload: dict, current_user=Depends(auth.get_current_user)):
    require_admin(current_user)

    content = payload.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Policy content cannot be empty")

    validate_yaml(content)

    try:
        if POLICY_PATH.exists():
            create_backup()
        write_policy_text(content)
        return {"message": "Policy updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")


@router.post("/reload")
async def reload_policy(current_user=Depends(auth.get_current_user)):
    require_admin(current_user)

    try:
        content = read_policy_text()
        validate_yaml(content)
        return {"message": "Policy reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload policy: {str(e)}")


@router.post("/reset")
async def reset_policy(current_user=Depends(auth.get_current_user)):
    require_admin(current_user)

    try:
        if DEFAULT_BACKUP_PATH.exists():
            shutil.copy2(DEFAULT_BACKUP_PATH, POLICY_PATH)
        else:
            raise FileNotFoundError("Default backup policy not found")

        return {"message": "Policy reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset policy: {str(e)}")


@router.get("/history")
async def get_policy_history(current_user=Depends(auth.get_current_user)):
    require_admin(current_user)

    try:
        versions = []
        for file in sorted(BACKUP_DIR.glob("*.yaml"), reverse=True):
            versions.append({
                "name": file.name,
                "timestamp": int(file.stat().st_mtime)
            })

        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")


@router.post("/restore")
async def restore_policy(payload: dict, current_user=Depends(auth.get_current_user)):
    require_admin(current_user)

    version = payload.get("version")
    if not version:
        raise HTTPException(status_code=400, detail="Version is required")

    restore_path = BACKUP_DIR / version
    if not restore_path.exists():
        raise HTTPException(status_code=404, detail="Requested version not found")

    try:
        if POLICY_PATH.exists():
            create_backup()
        shutil.copy2(restore_path, POLICY_PATH)
        return {"message": "Policy restored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore policy: {str(e)}")