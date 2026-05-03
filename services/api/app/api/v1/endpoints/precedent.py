from fastapi import APIRouter

router = APIRouter()

@router.get("/{clause_id}")
async def get_precedent(clause_id: str):
    return {"status": "not_implemented", "clause_id": clause_id}
