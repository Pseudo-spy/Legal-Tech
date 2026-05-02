from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def generate_counter_offer():
    return {"status": "not_implemented"}
