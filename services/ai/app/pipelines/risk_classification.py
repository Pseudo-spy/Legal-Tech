"""
Step 6.3 — Risk Classification Pipeline
Two-pass pipeline:
  Pass 1 — rule engine triages every clause into GREEN / YELLOW / RED
  Pass 2 — LLM analyses only YELLOW and RED clauses, in batches of ≤20
GREEN clauses receive default LOW/SAFE results without any LLM call.
The streaming variant yields ClauseResult objects one at a time.
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import AsyncIterator, Iterator, List, Optional, Sequence

from pydantic import BaseModel, Field, validator

from ..rules.regex_rules import RiskCategory
from ..rules.risk_mapper import (
    ClauseTriage,
    TriageLevel,
    partition_by_triage,
    triage_clauses,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRIMARY_MODEL    = "claude-sonnet-4-20250514"
MAX_BATCH_SIZE   = 20                           # clauses per LLM call
PROMPT_DIR       = __file__  # sibling; adjust to real prompt loader path


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class RiskSeverity(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class SafetyRating(str, Enum):
    SAFE     = "SAFE"
    CAUTION  = "CAUTION"
    DANGER   = "DANGER"


class ClauseResult(BaseModel):
    """Full analysis result for a single clause."""

    clause_index: int
    clause_text:  str
    triage:       str                    # GREEN / YELLOW / RED from rule engine
    risk_severity: RiskSeverity = RiskSeverity.LOW
    safety_rating: SafetyRating = SafetyRating.SAFE
    risk_categories: List[str]  = Field(default_factory=list)
    explanation:     str        = ""
    recommendation:  str        = ""
    power_imbalance: Optional[str] = None   # filled by later pipeline step
    llm_analysed:    bool       = False     # True if the LLM was called


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a contract risk analyst. "
    "You will receive a JSON array of contract clauses, each with an 'index' and 'text'. "
    "For EACH clause respond with a JSON array (same order, same length) where each element has:\n"
    "  index          – the clause index (integer)\n"
    "  risk_severity  – one of LOW, MEDIUM, HIGH, CRITICAL\n"
    "  safety_rating  – one of SAFE, CAUTION, DANGER\n"
    "  risk_categories – array of risk category strings\n"
    "  explanation    – 1–2 sentence explanation of the risk (plain text)\n"
    "  recommendation – 1 sentence actionable recommendation (plain text)\n"
    "Return ONLY the JSON array. No markdown, no preamble."
)


def _build_user_message(
    batch: List[ClauseTriage],
    contract_type: str,
    user_role: str,
) -> str:
    """Serialise a batch of clauses into the LLM user message."""
    clauses_payload = [
        {"index": ct.index, "text": ct.text}
        for ct in batch
    ]
    preamble = (
        f"Contract type: {contract_type}\n"
        f"Reviewing party role: {user_role}\n"
        f"Clauses to analyse:\n"
    )
    return preamble + json.dumps(clauses_payload, ensure_ascii=False)


def _parse_llm_response(
    raw: str,
    batch: List[ClauseTriage],
    contract_type: str,
) -> List[ClauseResult]:
    """
    Parse the LLM JSON array and merge it with the original ClauseTriage data.
    Falls back gracefully on parse errors.
    """
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        payload = json.loads(cleaned)
        if not isinstance(payload, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("LLM response parse error (%s); falling back to MEDIUM for entire batch", exc)
        return _fallback_results(batch)

    # Index the batch for quick lookup
    batch_by_index = {ct.index: ct for ct in batch}
    results: List[ClauseResult] = []

    for item in payload:
        idx = item.get("index")
        ct = batch_by_index.get(idx)
        if ct is None:
            logger.warning("LLM returned unknown index %s; skipping", idx)
            continue

        try:
            result = ClauseResult(
                clause_index=ct.index,
                clause_text=ct.text,
                triage=ct.result.triage.value,
                risk_severity=RiskSeverity(item.get("risk_severity", "MEDIUM")),
                safety_rating=SafetyRating(item.get("safety_rating", "CAUTION")),
                risk_categories=item.get("risk_categories", ct.result.categories),
                explanation=item.get("explanation", ""),
                recommendation=item.get("recommendation", ""),
                llm_analysed=True,
            )
        except Exception as exc:
            logger.warning("Pydantic validation failed for index %s (%s); using fallback", idx, exc)
            result = _fallback_single(ct)

        results.append(result)

    # Ensure every clause in the batch has a result
    returned_indices = {r.clause_index for r in results}
    for ct in batch:
        if ct.index not in returned_indices:
            results.append(_fallback_single(ct))

    return results


def _fallback_results(batch: List[ClauseTriage]) -> List[ClauseResult]:
    return [_fallback_single(ct) for ct in batch]


def _fallback_single(ct: ClauseTriage) -> ClauseResult:
    severity = RiskSeverity.HIGH if ct.result.triage == TriageLevel.RED else RiskSeverity.MEDIUM
    rating   = SafetyRating.DANGER if ct.result.triage == TriageLevel.RED else SafetyRating.CAUTION
    return ClauseResult(
        clause_index=ct.index,
        clause_text=ct.text,
        triage=ct.result.triage.value,
        risk_severity=severity,
        safety_rating=rating,
        risk_categories=ct.result.categories,
        explanation="Automated fallback — manual review recommended.",
        recommendation="Review with legal counsel.",
        llm_analysed=False,
    )


def _green_result(ct: ClauseTriage) -> ClauseResult:
    return ClauseResult(
        clause_index=ct.index,
        clause_text=ct.text,
        triage=TriageLevel.GREEN.value,
        risk_severity=RiskSeverity.LOW,
        safety_rating=SafetyRating.SAFE,
        risk_categories=[],
        explanation="No risk signals detected.",
        recommendation="No action required.",
        llm_analysed=False,
    )


# ---------------------------------------------------------------------------
# Batch splitter
# ---------------------------------------------------------------------------

def _batch(items: List[ClauseTriage], size: int) -> List[List[ClauseTriage]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# Synchronous pipeline
# ---------------------------------------------------------------------------

def run_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    anthropic_client=None,
) -> List[ClauseResult]:
    """
    Full two-pass risk classification (blocking / synchronous).

    Parameters
    ----------
    clauses:        Ordered list of clause text strings.
    contract_type:  Detected contract type (e.g. "Employment").
    user_role:      Reviewing party role (e.g. "employee").
    anthropic_client: An ``anthropic.Anthropic`` instance (optional).

    Returns
    -------
    List[ClauseResult] in clause index order.
    """
    import anthropic

    client = anthropic_client or anthropic.Anthropic()

    # ── Pass 1: Rule engine triage ─────────────────────────────────────
    triaged = triage_clauses(clauses)
    buckets = partition_by_triage(triaged)

    green_results: List[ClauseResult] = [_green_result(ct) for ct in buckets[TriageLevel.GREEN.value]]
    flagged = buckets[TriageLevel.YELLOW.value] + buckets[TriageLevel.RED.value]

    # ── Pass 2: LLM analysis of flagged clauses in batches ────────────
    llm_results: List[ClauseResult] = []
    for batch in _batch(flagged, MAX_BATCH_SIZE):
        logger.info(
            "Sending batch of %d clauses to LLM (indices %s–%s)",
            len(batch), batch[0].index, batch[-1].index,
        )
        user_msg = _build_user_message(batch, contract_type, user_role)
        response = client.messages.create(
            model=PRIMARY_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text
        llm_results.extend(_parse_llm_response(raw, batch, contract_type))

    # ── Merge and sort by original clause index ───────────────────────
    all_results = green_results + llm_results
    all_results.sort(key=lambda r: r.clause_index)
    return all_results


# ---------------------------------------------------------------------------
# Streaming pipeline (yields ClauseResult as they arrive)
# ---------------------------------------------------------------------------

def stream_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    anthropic_client=None,
) -> Iterator[ClauseResult]:
    """
    Streaming synchronous variant.
    Yields ClauseResult objects one at a time as each LLM batch completes.
    GREEN clauses are yielded immediately (before any LLM call).
    """
    import anthropic

    client = anthropic_client or anthropic.Anthropic()

    triaged = triage_clauses(clauses)
    buckets = partition_by_triage(triaged)

    # Yield GREEN results immediately
    for ct in buckets[TriageLevel.GREEN.value]:
        yield _green_result(ct)

    flagged = buckets[TriageLevel.YELLOW.value] + buckets[TriageLevel.RED.value]

    for batch in _batch(flagged, MAX_BATCH_SIZE):
        logger.info("Streaming batch of %d flagged clauses", len(batch))
        user_msg = _build_user_message(batch, contract_type, user_role)
        response = client.messages.create(
            model=PRIMARY_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text
        batch_results = _parse_llm_response(raw, batch, contract_type)
        for result in batch_results:
            yield result   # one at a time — SSE can push immediately


async def async_stream_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    async_client=None,
) -> AsyncIterator[ClauseResult]:
    """
    Async streaming variant for use in FastAPI / asyncio contexts.
    Yields ClauseResult objects as each LLM batch completes.
    """
    import anthropic

    client = async_client or anthropic.AsyncAnthropic()

    triaged = triage_clauses(clauses)
    buckets = partition_by_triage(triaged)

    for ct in buckets[TriageLevel.GREEN.value]:
        yield _green_result(ct)

    flagged = buckets[TriageLevel.YELLOW.value] + buckets[TriageLevel.RED.value]

    for batch in _batch(flagged, MAX_BATCH_SIZE):
        user_msg = _build_user_message(batch, contract_type, user_role)
        response = await client.messages.create(
            model=PRIMARY_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text
        for result in _parse_llm_response(raw, batch, contract_type):
            yield result