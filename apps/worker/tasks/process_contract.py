from celery_app import app
import asyncio

from app.parser.document_parser import parse_document
from app.parser.clause_segmenter import segment_clauses
from app.utils.file_loader import download_file


@app.task(bind=True)
def process_contract(self, contract_id: str, file_url: str):
    """
    Main scan pipeline task.
    """

    async def _run():
        try:
            # 1. Download
            file_bytes = download_file(file_url)

            # 2. Detect type
            file_type = file_url.split(".")[-1]

            # 3. Parse
            text = parse_document(file_bytes, file_type)

            # 4. Segment
            clauses = segment_clauses(text)

            print(f"[PROCESS] Contract: {contract_id}")
            print(f"[PROCESS] Text length: {len(text)}")
            print(f"[PROCESS] Clauses: {len(clauses)}")

            return {
                "contract_id": contract_id,
                "text_length": len(text),
                "clauses": len(clauses),
            }

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            raise e

    return asyncio.run(_run())