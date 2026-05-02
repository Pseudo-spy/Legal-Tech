from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_report():
    return {"status": "not_implemented"}

@router.get("/{report_id}")
async def get_report(report_id: str):
    return {"status": "not_implemented", "report_id": report_id}
