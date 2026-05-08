"""
STEP 7.2 — Power Asymmetry Pipeline
-------------------------------------
PURPOSE:
  This pipeline scores the "power imbalance" of an entire contract.
  Rather than looking at individual clauses, it takes the FULL picture
  (all clause results + their risk assessments) and produces a single
  integer score from -100 to +100:
      -100  = entirely one-sided against the user
         0  = perfectly balanced
      +100  = entirely in the user's favour

  It also surfaces key imbalances (specific problematic areas) and
  leverage points (what the user could negotiate on).

FLOW:
  [All Clause Results] → single AI call → parse PowerAsymmetryResult
  → store in analysis_results table → return result

HOW IT FITS IN:
  Called from the main Celery task AFTER consequence generation completes.
  Its output is stored to DB and also forwarded to the summary pipeline.
"""

import os
import json
import logging
from typing import List, Optional

import anthropic
from pydantic import BaseModel, field_validator

# Database import — replace with your actual ORM/session import
# from db.session import get_db_session
# from db.models import AnalysisResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ClauseResultInput(BaseModel):
    """
    Lightweight view of a clause result that this pipeline needs.
    The caller assembles this from the risk classification output.
    """
    clause_id:     str
    clause_type:   str
    clause_text:   str
    risk_level:    str   # "HIGH", "MEDIUM", "LOW"
    risk_category: str   # e.g. "Financial", "IP", "Liability"
    summary:       Optional[str] = None  # AI-generated plain-language summary


class KeyImbalance(BaseModel):
    """Represents one identified power imbalance in the contract."""
    area:        str   # e.g. "Termination Rights", "Liability Cap"
    description: str   # Plain-language explanation of why this is one-sided
    favors:      str   # "counterparty" or "user"


class PowerAsymmetryResult(BaseModel):
    """
    Full power asymmetry analysis for a contract.
    Stored to the analysis_results table after generation.
    """
    power_score:     int            # -100 to +100
    power_label:     str            # e.g. "Heavily Unfavourable", "Balanced", "Favourable"
    key_imbalances:  List[KeyImbalance]  # At least 1 for contracts with HIGH-risk clauses
    leverage_points: List[str]      # What the user can push back on during negotiation

    @field_validator("power_score")
    @classmethod
    def validate_power_score(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("power_score must be an integer")
        if not (-100 <= v <= 100):
            raise ValueError(f"power_score must be between -100 and +100, got {v}")
        return v

    @field_validator("key_imbalances")
    @classmethod
    def validate_imbalances(cls, v: List[KeyImbalance]) -> List[KeyImbalance]:
        # We allow empty list for low-risk contracts; caller validates HIGH-clause rule
        return v


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_power_asymmetry_prompt(
    clauses:   List[ClauseResultInput],
    user_role: str,
) -> str:
    """
    Builds the power_asymmetry.txt prompt by injecting clause data and user role.
    Serializes clause list as structured text so the model can reason over it.
    """
    clause_block = "\n\n".join(
        f"Clause {i+1} [{c.risk_level}] — {c.clause_type} ({c.risk_category}):\n{c.clause_text}"
        for i, c in enumerate(clauses)
    )

    return f"""You are an expert contract negotiation analyst. Assess the overall power
balance of this contract from the perspective of: {user_role}.

Analyze ALL clauses below holistically — consider which party has more rights,
fewer obligations, broader escape clauses, and stronger enforcement mechanisms.

CONTRACT CLAUSES:
{clause_block}

Respond ONLY with a valid JSON object — no markdown, no preamble.
Use this exact schema:
{{
  "power_score":     <integer from -100 (worst for user) to +100 (best for user)>,
  "power_label":     "<one of: Heavily Unfavourable | Unfavourable | Slightly Unfavourable | Balanced | Slightly Favourable | Favourable | Heavily Favourable>",
  "key_imbalances":  [
    {{
      "area":        "<contract area, e.g. Termination Rights>",
      "description": "<plain-language explanation>",
      "favors":      "<counterparty | user>"
    }}
  ],
  "leverage_points": [
    "<specific clause or right the user could negotiate>",
    ...
  ]
}}"""


# ---------------------------------------------------------------------------
# DB storage helper
# ---------------------------------------------------------------------------

def _store_in_db(analysis_id: str, result: PowerAsymmetryResult) -> None:
    """
    Persists the power asymmetry result to the analysis_results table.
    Replace the stub below with your actual ORM call.

    Schema expected:
      analysis_results(analysis_id TEXT, result_type TEXT, result_json JSONB)
    """
    # --- Replace with real DB logic ---
    # with get_db_session() as session:
    #     record = AnalysisResult(
    #         analysis_id  = analysis_id,
    #         result_type  = "power_asymmetry",
    #         result_json  = result.model_dump(),
    #     )
    #     session.add(record)
    #     session.commit()
    logger.info(
        "[DB STUB] Storing power asymmetry result for analysis_id=%s | score=%d",
        analysis_id, result.power_score,
    )


# ---------------------------------------------------------------------------
# Core pipeline function
# ---------------------------------------------------------------------------

def run_power_asymmetry(
    clauses:       List[ClauseResultInput],
    user_role:     str,
    analysis_id:   str,
    primary_model: str = "claude-sonnet-4-20250514",
) -> PowerAsymmetryResult:
    """
    Main entry point for the Power Asymmetry Pipeline.

    Steps:
      1. Build a comprehensive prompt using all clause results.
      2. Send a single AI model call to score the full contract.
      3. Parse and validate the response into a PowerAsymmetryResult.
      4. Store the result in the analysis_results table.
      5. Return the result for use in downstream pipelines.

    Args:
        clauses:       All clause results (all risk levels included for full context).
        user_role:     The user's role, e.g. "employee", "vendor", "contractor".
        analysis_id:   The DB record ID for this analysis (used for storage).
        primary_model: Anthropic model ID.

    Returns:
        PowerAsymmetryResult — the complete power asymmetry analysis.
    """
    logger.info(
        "Power asymmetry pipeline: analyzing %d clauses for role='%s'",
        len(clauses), user_role,
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = _build_power_asymmetry_prompt(clauses, user_role)

    try:
        # Step 2: Single AI call for the whole contract (holistic analysis)
        response = client.messages.create(
            model      = primary_model,
            max_tokens = 1200,
            messages   = [{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()

        # Step 3: Parse and validate
        raw_json = json.loads(raw_text)

        # Deserialise nested key_imbalances list
        raw_json["key_imbalances"] = [
            KeyImbalance(**item) for item in raw_json.get("key_imbalances", [])
        ]

        result = PowerAsymmetryResult(**raw_json)

        # Extra business rule: HIGH-risk contracts must have ≥1 key imbalance
        high_risk_count = sum(1 for c in clauses if c.risk_level == "HIGH")
        if high_risk_count > 0 and len(result.key_imbalances) == 0:
            logger.warning(
                "Contract has %d HIGH-risk clauses but 0 key_imbalances returned. "
                "Model may need a stronger prompt.",
                high_risk_count,
            )

        # Step 4: Persist to DB
        _store_in_db(analysis_id, result)

        logger.info(
            "✓ Power asymmetry complete: score=%d label='%s' imbalances=%d",
            result.power_score, result.power_label, len(result.key_imbalances),
        )
        return result

    except json.JSONDecodeError as e:
        logger.error("JSON parse error in power asymmetry pipeline: %s", e)
        raise
    except Exception as e:
        logger.error("Power asymmetry pipeline failed: %s", e)
        raise