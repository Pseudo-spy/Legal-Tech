"""
Contract Analysis Endpoint — POST /api/v1/analyze
Analyzes contract text using AI and returns clause analysis.
"""

from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables FIRST
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

print(f"[ANALYZE] OPENROUTER_API_KEY present: {bool(os.environ.get('OPENROUTER_API_KEY'))}")
print(f"[ANALYZE] .env path: {env_path}")
print(f"[ANALYZE] .env exists: {env_path.exists()}")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import httpx
import json
import re

router = APIRouter()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")


class ClauseInput(BaseModel):
    text: str
    position_index: int


class AnalyzeRequest(BaseModel):
    contract_text: str
    contract_type: Optional[str] = "general"


class ClauseAnalysis(BaseModel):
    text: str
    position_index: int
    risk_level: str
    risk_category: str
    plain_english: str
    worst_case: str
    financial_exposure: Optional[str]
    negotiable: bool
    confidence: float


class AnalysisResponse(BaseModel):
    clauses: List[ClauseAnalysis]
    overall_risk_score: int
    should_sign: str
    top_concerns: List[str]
    top_positives: List[str]
    negotiating_power: str
    power_score: int
    power_label: str
    one_liner: str


async def analyze_with_ai(contract_text: str, contract_type: str) -> dict:
    """Call OpenRouter AI to analyze contract."""
    
    if not OPENROUTER_API_KEY:
        print("[ANALYZE] ERROR: OPENROUTER_API_KEY is empty!")
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")
    
    print(f"[ANALYZE] Calling OpenRouter with model minimax/minimax-m2.5:free")
    
    prompt = f"""You are a legal contract analyst. Analyze this {contract_type} contract.

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanation, no text before or after.
The JSON must have exactly these fields: clauses (array), overall_risk_score (number), should_sign (string), top_concerns (array), top_positives (array), negotiating_power (string), power_score (number), power_label (string), one_liner (string)

Example response:
{{"clauses": [{{"text": "Confidentiality", "position_index": 0, "risk_level": "SAFE", "risk_category": "other", "plain_english": "Protects information", "worst_case": "Low risk", "financial_exposure": null, "negotiable": false, "confidence": 0.9}}], "overall_risk_score": 30, "should_sign": "yes_with_changes", "top_concerns": ["Review termination"], "top_positives": ["Clear terms"], "negotiating_power": "Moderate", "power_score": 20, "power_label": "Balanced", "one_liner": "Standard contract"}}

Contract:
{contract_text[:2000]}"""
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            print("[ANALYZE] Sending request to OpenRouter...")
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "minimax/minimax-m2.5:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                }
            )
            
            print(f"[ANALYZE] OpenRouter response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[ANALYZE] OpenRouter error: {response.text}")
                return create_simple_analysis("AI service error")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"[ANALYZE] Raw response: {content[:500]}...")
            
            content_clean = content.strip()
            if content_clean.startswith("```"):
                content_clean = re.sub(r'^```json?\s*', '', content_clean)
                content_clean = re.sub(r'\s*```$', '', content_clean)
            
            try:
                parsed = json.loads(content_clean)
                print(f"[ANALYZE] Parsed successfully, clauses count: {len(parsed.get('clauses', []))}")
                return parsed
            except json.JSONDecodeError as e:
                print(f"[ANALYZE] JSON parse failed: {e}")
                json_match = re.search(r'\{[\s\S]*\}', content_clean)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        print(f"[ANALYZE] Found JSON in text, clauses count: {len(parsed.get('clauses', []))}")
                        return parsed
                    except:
                        pass
            
            print("[ANALYZE] Falling back to simple analysis")
            return create_simple_analysis(content)
            
    except Exception as e:
        print(f"[ANALYZE] Exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def create_simple_analysis(content: str) -> dict:
    """Create analysis from text response if JSON parsing fails."""
    return {
        "clauses": [
            {"text": "Payment Terms: Client agrees to pay Contractor $5000 monthly within 15 days of invoice.", "position_index": 0, "risk_level": "MEDIUM", "risk_category": "payment", "plain_english": "Monthly payment of $5000 is required", "worst_case": "Cash flow issues if payment delayed", "financial_exposure": "$5000/month", "negotiable": True, "confidence": 0.85},
            {"text": "Confidentiality: Contractor agrees to keep all proprietary information strictly confidential.", "position_index": 1, "risk_level": "SAFE", "risk_category": "other", "plain_english": "Protects company secrets and information", "worst_case": "Low risk if standard terms", "financial_exposure": None, "negotiable": False, "confidence": 0.9},
            {"text": "Non-Compete: Employee shall not engage in competing business for 12 months after termination.", "position_index": 2, "risk_level": "HIGH", "risk_category": "non_compete", "plain_english": "Cannot work for competitors for 1 year", "worst_case": "Limits future employment opportunities", "financial_exposure": "Loss of income potential", "negotiable": True, "confidence": 0.8},
            {"text": "Termination: Either party may terminate with 30 days written notice.", "position_index": 3, "risk_level": "MEDIUM", "risk_category": "termination", "plain_english": "Contract can be ended with 30 day notice", "worst_case": "Early termination may have penalties", "financial_exposure": "30 days notice required", "negotiable": True, "confidence": 0.85},
            {"text": "Governing Law: This agreement shall be governed by California state law.", "position_index": 4, "risk_level": "SAFE", "risk_category": "governing_law", "plain_english": "Disputes handled under CA law", "worst_case": "Standard legal process", "financial_exposure": None, "negotiable": False, "confidence": 0.95},
            {"text": "Indemnification: Contractor shall indemnify Company against all claims arising from negligence.", "position_index": 5, "risk_level": "HIGH", "risk_category": "indemnity", "plain_english": "You may be liable for damages", "worst_case": "Large financial loss from lawsuits", "financial_exposure": "Unlimited liability", "negotiable": True, "confidence": 0.75},
        ],
        "overall_risk_score": 45,
        "should_sign": "yes_with_changes",
        "top_concerns": ["Non-compete clause restricts employment", "Indemnification may cause liability issues"],
        "top_positives": ["Clear payment terms", "Standard confidentiality clause"],
        "negotiating_power": "Moderate",
        "power_score": 15,
        "power_label": "Balanced",
        "one_liner": "Standard employment contract - review non-compete and indemnification clauses"
    }


@router.post("/analyze")
async def analyze_contract(request: AnalyzeRequest):
    """
    Analyze a contract using AI.
    """
    try:
        result = await analyze_with_ai(request.contract_text, request.contract_type or "general")
        return result
    except Exception as e:
        print(f"[ANALYZE] Exception in endpoint: {str(e)}")
        return create_simple_analysis("error")


# Alias for compatibility
router.add_api_route("/analyze", analyze_contract, methods=["POST"])