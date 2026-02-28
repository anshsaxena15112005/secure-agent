from fastapi import APIRouter, Depends, HTTPException, status
from backend.models import schemas
from backend.security import auth
import yaml
import os

router = APIRouter()

@router.post("/auth/login", response_model=schemas.Token)
async def login(credentials: schemas.LoginRequest):
    # In a real app, verify against a database
    if credentials.username == "admin" and credentials.password == "securepassword123":
        access_token = auth.create_access_token(data={"sub": credentials.username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/evaluate", response_model=schemas.PolicyEvaluationResponse)
async def evaluate_policy(request: schemas.PolicyEvaluationRequest, current_user: str = Depends(auth.get_current_user)):
    # A simple mock policy evaluation based on the yaml
    policy_path = os.path.join(os.path.dirname(__file__), '../../policies/default_policy.yaml')
    
    try:
        with open(policy_path, 'r') as file:
            policy = yaml.safe_load(file)
            
            # Simple check against the default policy
            allowed_actions = policy.get('default_role', {}).get('allowed_actions', [])
            if request.action in allowed_actions:
                return schemas.PolicyEvaluationResponse(allowed=True, reason="Matched allowed action in default policy")
            else:
                return schemas.PolicyEvaluationResponse(allowed=False, reason="Action not permitted by policy")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate policy: {str(e)}")
