"""
Q&A Chat Pipeline (STEP 8.2).
Uses LangChain with pgvector retriever for contract Q&A.
Streams answers with clause citations.
"""

import os
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.chat_models import (
    ChatOpenAI,
)  # Using OpenRouter via OpenAI-compatible API

from app.models.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "contract_qa"


def _get_vectorstore(contract_id: str):
    """
    Get PGVector vectorstore scoped to a specific contract_id.

    Uses the DATABASE_URL environment variable for connection.
    Filters by contract_id using the PGVector search_kwargs.
    """
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

    connection_string = os.environ.get("DATABASE_URL", "")
    # Convert asyncpg URL to standard postgresql for LangChain
    if "postgresql+asyncpg" in connection_string:
        connection_string = connection_string.replace(
            "postgresql+asyncpg", "postgresql"
        )

    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=connection_string,
        embedding_function=embeddings,
        use_jsonb=True,
    )


def _get_chat_model(streaming: bool = False):
    """
    Get LLM for chat.
    Uses OpenRouter via OpenAI-compatible API.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("FAST_MODEL", "google/gemini-2.0-flash-001")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE_URL,
        streaming=streaming,
        temperature=0.7,
    )


def _build_prompt_template() -> ChatPromptTemplate:
    """Build the chat prompt template with citation instructions."""
    system_template = """You are a contract analysis assistant. You help users understand their contracts.

RULES:
1. Always cite the specific clause or section you reference in your answer (e.g., "Section 4.2 states..." or "The clause about termination says...")
2. If the answer is NOT in the provided contract chunks, explicitly say "This topic is not addressed in the contract" - never fabricate contract terms.
3. Be concise and accurate. Use plain language.
4. If you reference a specific clause, include the clause text in your answer."""

    human_template = """Context (contract chunks):
{context}

Question: {question}

Remember to cite clauses and say if the topic is not in the contract."""

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template),
    ]

    return ChatPromptTemplate.from_messages(messages)


async def answer_question(
    contract_id: str,
    question: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AsyncGenerator[str, None]:
    """
    Answer a question about a contract using RAG.

    Parameters
    ----------
    contract_id : str
        UUID of the contract.
    question : str
        User's question.
    conversation_history : Optional[List[Dict[str, str]]]
        Previous Q&A pairs for context.

    Yields
    ------
    str
        Tokens of the answer as they are generated (streaming).
    """
    logger.info("Processing question for contract %s: %s", contract_id, question[:100])

    # Get vectorstore with contract-specific filter
    vectorstore = _get_vectorstore(contract_id)

    # Create retriever with contract_id filter
    search_kwargs = {
        "k": 5,
        "filter": {"contract_id": contract_id},
    }
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    # Get chat model with streaming
    chat_model = _get_chat_model(streaming=True)

    # Build prompt
    prompt = _build_prompt_template()

    # Setup memory if conversation history provided
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
    )

    if conversation_history:
        for msg in conversation_history:
            if msg.get("role") == "user":
                memory.chat_memory.add_user_message(msg.get("content", ""))
            elif msg.get("role") == "assistant":
                memory.chat_memory.add_ai_message(msg.get("content", ""))

    # Create the chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    # Run the chain and stream the response
    try:
        # Note: ConversationalRetrievalChain doesn't natively stream in older versions
        # We'll use a workaround: get the full response and yield it
        result = await chain.ainvoke({"question": question})

        answer = result.get("answer", "")
        source_documents = result.get("source_documents", [])

        # Stream the answer token by token (simple implementation)
        for char in answer:
            yield char

        # After streaming, yield the citation as a final event
        if source_documents:
            citation = "\n\n**Sources:**\n"
            for i, doc in enumerate(source_documents[:3], 1):
                citation += f"{i}. {doc.page_content[:200]}...\n"
            yield citation

    except Exception as e:
        logger.error("Chat pipeline error: %s", e)
        yield f"I encountered an error while processing your question: {str(e)}"
