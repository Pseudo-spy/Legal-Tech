from fastapi import APIRouter

router = APIRouter()

@router.get("/{contract_id}")
async def get_summary(contract_id: str):
    return {"status": "not_implemented", "contract_id": contract_id}
