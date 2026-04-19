from fastapi import APIRouter, HTTPException
from app.models.schemas import LoginRequest, Token

router = APIRouter()

# Simple static credentials for demo — replace with proper auth in production
DEMO_USERS = {
    "admin": "redteam2025",
    "operator": "mapper123",
}


@router.post("/login", response_model=Token)
async def login(req: LoginRequest):
    if DEMO_USERS.get(req.username) != req.password:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    # In production, generate a proper JWT
    return Token(access_token=f"demo_token_{req.username}", token_type="bearer")
