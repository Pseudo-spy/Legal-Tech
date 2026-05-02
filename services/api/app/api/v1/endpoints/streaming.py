from fastapi import APIRouter

router = APIRouter()

@router.get("/scan/{job_id}/stream")
async def stream_scan_results(job_id: str):
    return {"status": "not_implemented", "job_id": job_id}
