from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def start_scan():
    return {"status": "not_implemented"}


@router.get("/{job_id}")
async def get_scan_status(job_id: str):
    return {"status": "not_implemented", "job_id": job_id}
