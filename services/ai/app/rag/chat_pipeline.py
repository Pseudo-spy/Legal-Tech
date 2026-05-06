from app.multilingual.language_detector import detect_language
from app.multilingual.translator import (
    translate_to_english,
    translate_from_english,
)

from app.rag.retriever import retrieve_relevant_clauses


def answer_question(contract_id: str, question: str):
    detected_lang = detect_language(question)

    english_question = translate_to_english(
        question,
        detected_lang
    )

    clauses = retrieve_relevant_clauses(
        contract_id=contract_id,
        question=english_question
    )

    if not clauses:
        return "No relevant clauses found for this contract."

    context = "\n\n".join(clauses)

    answer = f"""
Question:
{question}

Relevant Clauses:
{context}
"""

    translated_answer = translate_from_english(
        answer,
        detected_lang
    )

    return translated_answer