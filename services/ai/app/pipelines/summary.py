"""
STEP 7.3 — Summary Card Pipeline
-----------------------------------
PURPOSE:
  This pipeline generates two outputs that act as the "executive summary"
  of a contract analysis:

  1. SUMMARY CARD — a plain-language card telling the user:
     • A one-liner verdict on the contract
     • Whether they should sign (and under what conditions)
     • The top 3 concerns and top 2 positives
     • An overall risk score (0-100)
     • Their negotiating power (Strong / Moderate / Weak)

  2. PROS vs CONS SNAPSHOT — a structured list of pros and cons,
     each tagged with a dimension label (Financial, Liability, IP, etc.),
     plus a final verdict string.

  Uses the FAST_MODEL (e.g. claude-haiku) because this is a summarisation
  task over already-processed data — speed matters here.

FLOW:
  [HIGH/MEDIUM summaries + risk stats] → AI call (FAST_MODEL)
  → SummaryCard + ProsConsSnapshot → store in analysis_results → return both

HOW IT FITS IN:
  Called from the main Celery task AFTER power analysis completes.
  Its output is the primary data shown on the front-end report card.
"""

import os
import json
import logging
from typing import List

import anthropic
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RiskStats(BaseModel):
    """Counts of clauses at each risk level — passed in from the classifier."""
    high_count:   int
    medium_count: int
    low_count:    int
    total_count:  int


class ProConItem(BaseModel):
    """A single pro or con with a dimension tag for front-end filtering."""
    dimension: str   # e.g. "Financial", "Liability", "IP", "Termination", "Compliance"
    text:      str   # Plain-language description


class SummaryCard(BaseModel):
    """
    The main summary card shown to the user at the top of the report.
    All fields are intentionally plain-language — no legalese.
    """
    one_liner:         str   # e.g. "This contract heavily favours the employer."
    should_you_sign:   str   # One of: "Yes as-is" | "Yes with changes" | "No"
    top_3_concerns:    List[str]   # Exactly 3 items
    top_2_positives:   List[str]   # Exactly 2 items
    overall_risk_score: int        # 0 (safe) to 100 (extremely risky)
    negotiating_power: str         # One of: "Strong" | "Moderate" | "Weak"

    @field_validator("should_you_sign")
    @classmethod
    def validate_sign(cls, v: str) -> str:
        allowed = {"Yes as-is", "Yes with changes", "No"}
        if v not in allowed:
            raise ValueError(f"should_you_sign must be one of {allowed}, got '{v}'")
        return v

    @field_validator("overall_risk_score")
    @classmethod
    def validate_risk_score(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError(f"overall_risk_score must be 0-100, got {v}")
        return v

    @field_validator("negotiating_power")
    @classmethod
    def validate_negotiating_power(cls, v: str) -> str:
        allowed = {"Strong", "Moderate", "Weak"}
        if v not in allowed:
            raise ValueError(f"negotiating_power must be one of {allowed}, got '{v}'")
        return v

    @field_validator("top_3_concerns")
    @classmethod
    def validate_concerns(cls, v: List[str]) -> List[str]:
        if len(v) != 3:
            raise ValueError(f"top_3_concerns must have exactly 3 items, got {len(v)}")
        return v

    @field_validator("top_2_positives")
    @classmethod
    def validate_positives(cls, v: List[str]) -> List[str]:
        if len(v) != 2:
            raise ValueError(f"top_2_positives must have exactly 2 items, got {len(v)}")
        return v


class ProsConsSnapshot(BaseModel):
    """
    The Pros vs Cons snapshot shown below the summary card.
    Each item carries a dimension label so the UI can colour-code them.
    """
    pros:    List[ProConItem]   # Positive aspects of the contract
    cons:    List[ProConItem]   # Negative / risky aspects
    verdict: str                # Short closing verdict, e.g. "Negotiate before signing."


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_summary_prompt(
    contract_type:    str,
    high_summaries:   List[str],
    medium_summaries: List[str],
    stats:            RiskStats,
) -> str:
    """
    Injects contract data into the summary.txt prompt template.
    """
    high_block   = "\n".join(f"- {s}" for s in high_summaries)   or "None"
    medium_block = "\n".join(f"- {s}" for s in medium_summaries) or "None"

    return f"""You are a contract analyst writing a plain-language report for a non-lawyer.

Contract Type: {contract_type}
Risk Statistics: {stats.high_count} HIGH | {stats.medium_count} MEDIUM | {stats.low_count} LOW | {stats.total_count} TOTAL

HIGH-Risk Clause Summaries:
{high_block}

MEDIUM-Risk Clause Summaries:
{medium_block}

Respond ONLY with a valid JSON object — no markdown, no explanation.
{{
  "one_liner":           "<single sentence verdict on this contract>",
  "should_you_sign":     "<exactly one of: Yes as-is | Yes with changes | No>",
  "top_3_concerns":      ["<concern 1>", "<concern 2>", "<concern 3>"],
  "top_2_positives":     ["<positive 1>", "<positive 2>"],
  "overall_risk_score":  <integer 0-100>,
  "negotiating_power":   "<exactly one of: Strong | Moderate | Weak>"
}}"""


def _build_pros_cons_prompt(
    high_summaries:   List[str],
    medium_summaries: List[str],
    low_summaries:    List[str],
) -> str:
    """
    Injects clause analysis into the pros/cons prompt template.
    """
    all_clauses = (
        "\n".join(f"[HIGH] {s}"   for s in high_summaries)
        + "\n"
        + "\n".join(f"[MEDIUM] {s}" for s in medium_summaries)
        + "\n"
        + "\n".join(f"[LOW] {s}"    for s in low_summaries)
    ).strip()

    return f"""You are a contract analyst. Based on the clause summaries below,
generate a structured Pros vs Cons breakdown. Each item MUST have a dimension tag.

Allowed dimension tags: Financial, Liability, IP, Termination, Compliance, Privacy, Scope, Other

Clause Summaries:
{all_clauses}

Respond ONLY with a valid JSON object — no markdown, no preamble.
{{
  "pros": [
    {{"dimension": "<tag>", "text": "<plain-language benefit>"}},
    ...
  ],
  "cons": [
    {{"dimension": "<tag>", "text": "<plain-language risk>"}},
    ...
  ],
  "verdict": "<short closing sentence>"
}}"""


# ---------------------------------------------------------------------------
# DB storage helper
# ---------------------------------------------------------------------------

def _store_in_db(
    analysis_id:   str,
    summary:       SummaryCard,
    pros_cons:     ProsConsSnapshot,
) -> None:
    """
    Persists both the summary card and pros/cons snapshot to analysis_results.
    Replace the stub with your actual ORM call.
    """
    # with get_db_session() as session:
    #     session.add(AnalysisResult(analysis_id=analysis_id,
    #                                result_type="summary_card",
    #                                result_json=summary.model_dump()))
    #     session.add(AnalysisResult(analysis_id=analysis_id,
    #                                result_type="pros_cons_snapshot",
    #                                result_json=pros_cons.model_dump()))
    #     session.commit()
    logger.info(
        "[DB STUB] Storing summary card + pros/cons for analysis_id=%s | "
        "risk_score=%d sign='%s'",
        analysis_id, summary.overall_risk_score, summary.should_you_sign,
    )


# ---------------------------------------------------------------------------
# Core pipeline function
# ---------------------------------------------------------------------------

def run_summary(
    contract_type:    str,
    high_summaries:   List[str],
    medium_summaries: List[str],
    low_summaries:    List[str],
    stats:            RiskStats,
    analysis_id:      str,
    fast_model:       str = "claude-haiku-4-5-20251001",
) -> tuple[SummaryCard, ProsConsSnapshot]:
    """
    Main entry point for the Summary Card Pipeline.

    Makes TWO sequential AI calls:
      Call 1 → SummaryCard  (the headline report card)
      Call 2 → ProsConsSnapshot  (the detailed pros/cons breakdown)

    Both use the FAST_MODEL because they summarise pre-processed data
    and latency is user-facing.

    Args:
        contract_type:    e.g. "Employment Agreement", "SaaS License"
        high_summaries:   Plain-language summaries of HIGH-risk clauses
        medium_summaries: Plain-language summaries of MEDIUM-risk clauses
        low_summaries:    Plain-language summaries of LOW-risk clauses
        stats:            Clause counts per risk level
        analysis_id:      DB record ID for this analysis
        fast_model:       Anthropic model ID (defaults to Haiku for speed)

    Returns:
        Tuple of (SummaryCard, ProsConsSnapshot)
    """
    logger.info(
        "Summary pipeline: contract_type='%s' H=%d M=%d L=%d",
        contract_type, stats.high_count, stats.medium_count, stats.low_count,
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ---- Call 1: Summary Card ------------------------------------------------
    try:
        summary_prompt = _build_summary_prompt(
            contract_type, high_summaries, medium_summaries, stats
        )
        resp1 = client.messages.create(
            model      = fast_model,
            max_tokens = 700,
            messages   = [{"role": "user", "content": summary_prompt}],
        )
        summary = SummaryCard(**json.loads(resp1.content[0].text.strip()))
        logger.info("✓ Summary card generated: sign='%s' score=%d",
                    summary.should_you_sign, summary.overall_risk_score)
    except Exception as e:
        logger.error("Summary card generation failed: %s", e)
        raise

    # ---- Call 2: Pros vs Cons ------------------------------------------------
    try:
        pros_cons_prompt = _build_pros_cons_prompt(
            high_summaries, medium_summaries, low_summaries
        )
        resp2 = client.messages.create(
            model      = fast_model,
            max_tokens = 800,
            messages   = [{"role": "user", "content": pros_cons_prompt}],
        )
        raw2     = json.loads(resp2.content[0].text.strip())

        # Deserialise nested ProConItem lists
        raw2["pros"] = [ProConItem(**p) for p in raw2.get("pros", [])]
        raw2["cons"] = [ProConItem(**c) for c in raw2.get("cons", [])]

        pros_cons = ProsConsSnapshot(**raw2)
        logger.info("✓ Pros/cons generated: %d pros, %d cons",
                    len(pros_cons.pros), len(pros_cons.cons))
    except Exception as e:
        logger.error("Pros/cons generation failed: %s", e)
        raise

    # ---- Store both results in DB -------------------------------------------
    _store_in_db(analysis_id, summary, pros_cons)

    return summary, pros_cons