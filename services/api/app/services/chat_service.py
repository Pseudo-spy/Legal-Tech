"""
Chat service — orchestration logic for Q&A chat.
Formats conversation history and calls the chat pipeline.
"""

import logging
from typing import List, Dict, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.repositories import contract_repo
from app.models.contract import Contract

logger = logging.getLogger(__name__)


async def verify_contract_and_get_id(
    db: AsyncSession,
    contract_id_str: str,
    user_id: str,
) -> UUID | None:
    """
    Verify contract exists and belongs to user.
    Returns contract_id UUID if valid, None otherwise.
    """
    try:
        contract_id = UUID(contract_id_str)
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    contract = await contract_repo.get_contract_by_id(db, contract_id, user_uuid)

    if not contract:
        return None

    return contract_id


async def check_embeddings_exist(
    contract_id: UUID,
) -> bool:
    """
    Check if embeddings exist for this contract.
    """
    # Use sync connection for simplicity
    import os
    from sqlalchemy import create_engine, text

    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg", "postgresql"
    )
    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """SELECT COUNT(*) FROM embeddings 
                   WHERE contract_id = :contract_id 
                   AND embedding_type = 'contract_qa'"""
            ),
            {"contract_id": str(contract_id)},
        )
        count = result.scalar_one()
        return count > 0


def format_conversation_history(
    history: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Format conversation history for the chat pipeline.
    Converts to LangChain message format if needed.
    """
    if not history:
        return []

    # Ensure proper format: [{"role": "user", "content": "..."}, ...]
    formatted = []
    for msg in history:
        if "role" in msg and "content" in msg:
            formatted.append({"role": msg["role"], "content": msg["content"]})
    return formatted


async def stream_chat_response(
    contract_id: str,
    question: str,
    conversation_history: List[Dict[str, str]] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream chat response using the AI chat pipeline.
    """
    logger.info("Streaming chat response for contract %s", contract_id)

    try:
        from services.ai.app.rag.chat_pipeline import answer_question

        # Convert conversation history to format expected by pipeline
        history = format_conversation_history(conversation_history or [])

        # Call the pipeline (which should be async and streaming)
        async for token in answer_question(contract_id, question, history):
            yield token

    except Exception as e:
        logger.error("Chat streaming error: %s", e)
        yield f"Error: {str(e)}"
