import re
from typing import List

def segment_clauses(text: str) -> List[str]:
    """
    Split document into clauses using basic heuristics.
    """
    if not text:
        return []

    clauses = re.split(r"\n+|\d+\.\s", text)

    clauses = [c.strip() for c in clauses if c.strip()]

    return clauses