"""
Step 6.1 — Contract Type Detection Pipeline
Detects contract type from the first 1000 tokens of text using a fast LLM.
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — swap these with your real model constants / env vars
# ---------------------------------------------------------------------------
FAST_MODEL = "claude-haiku-4-5-20251001"          # fastest / cheapest model
MAX_DETECTION_TOKENS = 1_000                       # token budget for input
CONFIDENCE_THRESHOLD = 0.80                        # flag below this value
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "type_detection.txt"


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class ContractType(str, Enum):
    EMPLOYMENT          = "Employment"
    NDA                 = "NDA"
    SERVICE_AGREEMENT   = "Service Agreement"
    VENDOR              = "Vendor"
    SAAS                = "SaaS"
    LEASE               = "Lease"
    PARTNERSHIP         = "Partnership"
    LOAN                = "Loan"
    IP_ASSIGNMENT       = "IP Assignment"
    SETTLEMENT          = "Settlement"
    UNKNOWN             = "Unknown"


class TypeDetectionResult(BaseModel):
    """Structured result returned by the type-detection pipeline."""

    type: ContractType = Field(..., description="Detected contract type")
    confidence: float  = Field(..., ge=0.0, le=1.0, description="Detection confidence 0–1")
    party_roles: List[str] = Field(default_factory=list, description="Roles of the signing parties")
    needs_manual_review: bool = Field(
        False,
        description="True when confidence < CONFIDENCE_THRESHOLD; the frontend should show the correction selector",
    )
    raw_excerpt: Optional[str] = Field(
        None,
        description="The first-1000-token excerpt sent to the model (for debugging)",
        exclude=True,
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.confidence < CONFIDENCE_THRESHOLD:
            object.__setattr__(self, 'needs_manual_review', True)


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _load_prompt_template() -> str:
    """Load the system prompt from disk (falls back to an inline default)."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    # Inline fallback so the pipeline works even without the prompt file
    return (
        "You are a contract-classification assistant. "
        "Analyse the contract excerpt provided by the user and respond ONLY with a "
        "JSON object (no markdown fences) with these keys:\n"
        "  type        – one of: Employment, NDA, Service Agreement, Vendor, SaaS, "
        "Lease, Partnership, Loan, IP Assignment, Settlement, Unknown\n"
        "  confidence  – float 0.0–1.0\n"
        "  party_roles – array of short role strings (e.g. ['employer','employee'])\n"
        "Be concise and accurate."
    )


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Rough token truncation (4 chars ≈ 1 token).
    Replace with a real tokeniser (tiktoken / anthropic-tokenizer) if needed.
    """
    char_limit = max_tokens * 4
    return text[:char_limit]


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def detect_contract_type(
    contract_text: str,
    *,
    anthropic_client=None,   # pass an already-constructed anthropic.Anthropic()
) -> TypeDetectionResult:
    """
    Detect the contract type from the first 1000 tokens of *contract_text*.

    Parameters
    ----------
    contract_text:
        Full or partial contract text.
    anthropic_client:
        An ``anthropic.Anthropic`` (or ``anthropic.AsyncAnthropic``) client.
        If ``None`` the function constructs one from the environment variable
        ``ANTHROPIC_API_KEY``.

    Returns
    -------
    TypeDetectionResult
        Pydantic model with type, confidence, party_roles, needs_manual_review.
    """
    import anthropic  # local import — keeps the module importable without the SDK

    client = anthropic_client or anthropic.Anthropic()
    excerpt = _truncate_to_tokens(contract_text, MAX_DETECTION_TOKENS)
    system_prompt = _load_prompt_template()

    logger.debug("Sending %d chars to %s for type detection", len(excerpt), FAST_MODEL)

    message = client.messages.create(
        model=FAST_MODEL,
        max_tokens=256,
        system=system_prompt,
        messages=[{"role": "user", "content": excerpt}],
    )

    raw_content = message.content[0].text.strip()
    logger.debug("Raw type-detection response: %s", raw_content)

    return _parse_response(raw_content, excerpt)


async def detect_contract_type_async(
    contract_text: str,
    *,
    async_client=None,
) -> TypeDetectionResult:
    """Async variant for use inside async frameworks (FastAPI, etc.)."""
    import anthropic

    client = async_client or anthropic.AsyncAnthropic()
    excerpt = _truncate_to_tokens(contract_text, MAX_DETECTION_TOKENS)
    system_prompt = _load_prompt_template()

    message = await client.messages.create(
        model=FAST_MODEL,
        max_tokens=256,
        system=system_prompt,
        messages=[{"role": "user", "content": excerpt}],
    )

    raw_content = message.content[0].text.strip()
    return _parse_response(raw_content, excerpt)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_response(raw: str, excerpt: str) -> TypeDetectionResult:
    """
    Parse the model's JSON response into a ``TypeDetectionResult``.

    Falls back gracefully on malformed responses instead of raising.
    """
    # Strip accidental markdown fences
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Type-detection returned non-JSON; defaulting to Unknown. raw=%r", raw)
        return TypeDetectionResult(
            type=ContractType.UNKNOWN,
            confidence=0.0,
            party_roles=[],
            raw_excerpt=excerpt,
        )

    # Normalise contract type
    raw_type = payload.get("type", "Unknown")
    try:
        contract_type = ContractType(raw_type)
    except ValueError:
        # Try case-insensitive match
        contract_type = _fuzzy_match_type(raw_type)

    confidence = float(payload.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))  # clamp to [0, 1]

    roles = payload.get("party_roles", [])
    if not isinstance(roles, list):
        roles = [str(roles)]

    result = TypeDetectionResult(
        type=contract_type,
        confidence=confidence,
        party_roles=[str(r) for r in roles],
        raw_excerpt=excerpt,
    )
    logger.info(
        "Type detection: type=%s confidence=%.2f needs_review=%s roles=%s",
        result.type,
        result.confidence,
        result.needs_manual_review,
        result.party_roles,
    )
    return result


def _fuzzy_match_type(raw: str) -> ContractType:
    """Best-effort case-insensitive match to a known ContractType."""
    normalised = raw.strip().lower()
    for member in ContractType:
        if member.value.lower() == normalised:
            return member
    # Partial match heuristics
    if "employ" in normalised:
        return ContractType.EMPLOYMENT
    if "non-disclos" in normalised or "nda" in normalised or "confidential" in normalised:
        return ContractType.NDA
    if "service" in normalised:
        return ContractType.SERVICE_AGREEMENT
    if "vendor" in normalised or "supplier" in normalised:
        return ContractType.VENDOR
    if "saas" in normalised or "software" in normalised or "subscription" in normalised:
        return ContractType.SAAS
    if "lease" in normalised or "rental" in normalised:
        return ContractType.LEASE
    if "partner" in normalised or "joint venture" in normalised:
        return ContractType.PARTNERSHIP
    if "loan" in normalised or "credit" in normalised or "promissory" in normalised:
        return ContractType.LOAN
    if "ip " in normalised or "intellectual property" in normalised or "patent" in normalised:
        return ContractType.IP_ASSIGNMENT
    if "settlement" in normalised or "release of claims" in normalised:
        return ContractType.SETTLEMENT
    return ContractType.UNKNOWN