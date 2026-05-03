from fastapi import APIRouter

router = APIRouter()

@router.post("/{contract_id}")
async def chat_with_contract(contract_id: str):
    return {"status": "not_implemented", "contract_id": contract_id}
