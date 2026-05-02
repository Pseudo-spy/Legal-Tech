from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id

router = APIRouter()

@router.get("/")
async def get_contracts(user_id: str = Depends(get_current_user_id)):
    """Placeholder endpoint to test authentication."""
    return {"message": "Success", "user_id": user_id, "contracts": []}
