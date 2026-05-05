from typing import Tuple
import fitz
from docx import Document
from io import BytesIO


def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF using multiple fallback strategies.
    """

    text_chunks = []

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise Exception(f"Failed to open PDF: {e}")

    for page in doc:
        page_text = ""

        try:
            page_text = page.get_text("text") or ""
        except Exception:
            page_text = ""

        if len(page_text.strip()) < 20:
            try:
                blocks = page.get_text("blocks") or []
                block_texts = []

                for b in blocks:
                    if len(b) > 4:
                        content = b[4]

                        # ensure it's string
                        if isinstance(content, str) and content.strip():
                            block_texts.append(content)

                page_text = " ".join(block_texts)
            except Exception:
                pass

        if len(page_text.strip()) < 10:
            try:
                words = page.get_text("words") or []
                word_texts = []

                for w in words:
                    if len(w) > 4:
                        content = w[4]
                        if isinstance(content, str):
                            word_texts.append(content)

                page_text = " ".join(word_texts)
            except Exception:
                pass

        text_chunks.append(page_text)

    full_text = "\n".join(text_chunks)

    if len(full_text.strip()) < 50:
        print("[WARNING] Very low text extracted — possible scanned or unsupported PDF")

    return full_text


def parse_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX.
    """
    try:
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {e}")


def parse_document(file_bytes: bytes, file_type: str) -> str:
    """
    Dispatch parser based on file type.
    """
    file_type = file_type.lower()

    if file_type == "pdf":
        return parse_pdf(file_bytes)

    elif file_type == "docx":
        return parse_docx(file_bytes)

    else:
        raise ValueError(f"Unsupported file type: {file_type}")