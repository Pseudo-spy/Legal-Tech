"""
Chat Endpoint — POST /api/v1/chat/{contractId}
Implements STEP 8.2: Q&A chat with streaming SSE response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from services.api.app.api.deps import get_current_user, get_db
from services.api.app.models.user import User

from services.api.app.services.chat_service import (
    verify_contract_and_get_id,
    check_embeddings_exist,
    stream_chat_response,
)

router = APIRouter()


@router.post("/{contract_id}")
async def chat_with_contract(
    contract_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream chat response for a contract Q&A.

    - Verifies JWT and ownership
    - Checks that embeddings exist for the contract
    - Streams the answer via SSE
    """
    # Verify contract and ownership
    contract_uuid = await verify_contract_and_get_id(
        db, contract_id, str(current_user.id)
    )
    if not contract_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or access denied",
        )

    # Check embeddings exist
    embeddings_exist = await check_embeddings_exist(contract_uuid)
    if not embeddings_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract not yet embedded. Please wait for scan to complete.",
        )

    question = request.get("question", "")
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required",
        )

    conversation_history = request.get("conversation_history", [])

    # Stream the response
    return StreamingResponse(
        stream_chat_response(str(contract_uuid), question, conversation_history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
