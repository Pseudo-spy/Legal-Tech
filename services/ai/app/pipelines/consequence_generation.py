"""
STEP 7.1 — Consequence Generation Pipeline
-------------------------------------------
PURPOSE:
  This pipeline acts as a "real-world translator" for legal risk.
  It takes HIGH and MEDIUM risk clauses (already classified) and,
  for each clause, calls the AI model to generate a plain-language
  consequence — including a headline, a realistic scenario, estimated
  financial exposure, probability of harm, and a similar real-world case.

FLOW:
  [Classified Clauses] → filter HIGH/MEDIUM → AI call per clause
  → parse into ConsequenceResult → return list of consequence objects

HOW IT FITS IN:
  Called from the main Celery task AFTER risk classification completes.
  Its output feeds into the power analysis and summary pipelines.
"""

import os
import json
import logging
from typing import List, Optional
from enum import Enum

import anthropic
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

class ClauseInput(BaseModel):
    """Represents a single classified clause passed into this pipeline."""
    clause_id:      str
    clause_type:    str           # e.g. "indemnity", "non-compete", "ip_assignment"
    clause_text:    str
    risk_level:     RiskLevel
    risk_category:  str           # e.g. "Financial", "IP", "Liability"
    user_role:      str           # e.g. "employee", "vendor", "contractor"
    contract_value: Optional[str] = None  # e.g. "$250,000" or None if unknown


class ConsequenceResult(BaseModel):
    """
    Parsed consequence object returned for each HIGH/MEDIUM clause.
    All fields come directly from the AI model response.
    """
    clause_id:          str
    clause_type:        str
    headline:           str   # Short, punchy summary of the risk
    scenario:           str   # A realistic paragraph describing what could go wrong
    financial_exposure: str   # Dollar amount like "$50,000" or "unlimited"
    probability:        str   # One of: "Low", "Medium", "High"
    similar_case:       str   # Brief reference to a real or illustrative case

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: str) -> str:
        # Enforce the three allowed probability values
        allowed = {"Low", "Medium", "High"}
        if v not in allowed:
            raise ValueError(f"probability must be one of {allowed}, got '{v}'")
        return v

    @field_validator("financial_exposure")
    @classmethod
    def validate_financial_exposure(cls, v: str) -> str:
        # Must either contain a "$" sign or be the literal string "unlimited"
        if v.lower() != "unlimited" and "$" not in v:
            raise ValueError(
                f"financial_exposure must be a dollar amount or 'unlimited', got '{v}'"
            )
        return v


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_consequence_prompt(clause: ClauseInput) -> str:
    """
    Injects clause details into the consequence.txt prompt template.
    We embed the template inline here for portability; in production
    you'd load it from prompts/consequence.txt.
    """
    contract_value_line = (
        f"Contract Value: {clause.contract_value}"
        if clause.contract_value
        else "Contract Value: Not specified"
    )

    return f"""You are a senior legal risk analyst. Analyze the following contract clause
and explain its real-world consequences in plain language.

Clause Type:      {clause.clause_type}
User Role:        {clause.user_role}
{contract_value_line}
Risk Category:    {clause.risk_category}

Clause Text:
\"\"\"{clause.clause_text}\"\"\"

Respond ONLY with a valid JSON object — no markdown, no explanation outside JSON.
Use this exact schema:
{{
  "headline":           "<one sentence summary of the risk>",
  "scenario":           "<2-3 sentence realistic scenario of what could go wrong>",
  "financial_exposure": "<dollar amount like '$50,000' or 'unlimited'>",
  "probability":        "<one of: Low | Medium | High>",
  "similar_case":       "<brief reference to a real or illustrative legal case>"
}}"""


# ---------------------------------------------------------------------------
# Core pipeline function
# ---------------------------------------------------------------------------

def run_consequence_generation(
    clauses:       List[ClauseInput],
    primary_model: str = "claude-sonnet-4-20250514",
) -> List[ConsequenceResult]:
    """
    Main entry point for the Consequence Generation Pipeline.

    Steps:
      1. Filter out LOW-risk clauses (they don't need consequence analysis).
      2. For each remaining clause, call the AI model with a tailored prompt.
      3. Parse and validate the JSON response into a ConsequenceResult object.
      4. Return the full list of consequence results.

    Args:
        clauses:       List of ClauseInput objects (all risk levels accepted;
                       LOW will be silently skipped).
        primary_model: Anthropic model ID to use for generation.

    Returns:
        List[ConsequenceResult] — one entry per HIGH/MEDIUM clause.
    """

    # Step 1: Filter — only HIGH and MEDIUM clauses go through this pipeline
    eligible = [c for c in clauses if c.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)]
    logger.info(
        "Consequence pipeline: %d total clauses → %d eligible (HIGH/MEDIUM), "
        "%d LOW skipped",
        len(clauses), len(eligible), len(clauses) - len(eligible),
    )

    if not eligible:
        return []

    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    results: List[ConsequenceResult] = []

    for clause in eligible:
        logger.debug("Generating consequence for clause_id=%s type=%s",
                     clause.clause_id, clause.clause_type)

        prompt = _build_consequence_prompt(clause)

        try:
            # Step 2: Call the primary AI model
            response = client.messages.create(
                model      = primary_model,
                max_tokens = 800,
                messages   = [{"role": "user", "content": prompt}],
            )

            raw_text = response.content[0].text.strip()

            # Step 3: Parse JSON response
            raw_json = json.loads(raw_text)

            # Step 4: Validate with Pydantic (raises ValidationError on bad data)
            result = ConsequenceResult(
                clause_id   = clause.clause_id,
                clause_type = clause.clause_type,
                **raw_json,
            )
            results.append(result)
            logger.info("✓ Consequence generated for clause_id=%s", clause.clause_id)

        except json.JSONDecodeError as e:
            logger.error("JSON parse error for clause_id=%s: %s", clause.clause_id, e)
            raise
        except Exception as e:
            logger.error("Consequence generation failed for clause_id=%s: %s",
                         clause.clause_id, e)
            raise

    logger.info("Consequence pipeline complete: %d results", len(results))
    return results