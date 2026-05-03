from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user_id
from app.db.session import get_async_session
from app.repositories import contract_repo, user_repo

router = APIRouter()


@router.get("/")
async def get_contracts(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    """Get all contracts for the authenticated user."""
    # Get internal user by Clerk ID
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        return {"message": "Success", "user_id": user_id, "contracts": []}

    # Get all contracts for this user
    contracts = await contract_repo.get_all_contracts_by_user_id(db, user.id)

    return {
        "message": "Success",
        "user_id": user_id,
        "contracts": [
            {
                "id": str(c.id),
                "original_filename": c.original_filename,
                "file_type": c.file_type,
                "detected_language": c.detected_language,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in contracts
        ],
    }
