from app.rag.retriever import retrieve_relevant_clauses


def answer_question(contract_id: str, question: str):
    clauses = retrieve_relevant_clauses(
        contract_id=contract_id,
        question=question
    )

    if not clauses:
        return "No relevant clauses found for this contract."

    context = "\n\n".join(clauses)

    return f"""
Question:
{question}

Relevant Clauses:
{context}
"""