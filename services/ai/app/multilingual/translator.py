"""
DeepL Translator (STEP 9.1).
Replaces deep_translator (Google) with deepl for superior legal terminology.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Initialize DeepL translator
_deepl_translator = None


def _get_translator():
    """Lazy-load DeepL translator."""
    global _deepl_translator
    if _deepl_translator is None:
        try:
            import deepl

            api_key = os.getenv("DEEPL_API_KEY", "")
            if not api_key:
                logger.warning(
                    "DEEPL_API_KEY not set. Translation will return original text."
                )
                return None
            _deepl_translator = deepl.Translator(api_key)
        except ImportError:
            logger.error("deepl package not installed. Run: pip install deepl")
            return None
    return _deepl_translator


def _load_legal_glossary() -> Dict[str, Dict[str, str]]:
    """Load legal glossary from JSON file."""
    import json
    from pathlib import Path

    glossary_path = Path(__file__).parent / "legal_glossary.json"
    if not glossary_path.exists():
        logger.warning("legal_glossary.json not found at %s", glossary_path)
        return {}

    try:
        return json.loads(glossary_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to load legal glossary: %s", e)
        return {}


# Cache glossary
_legal_glossary = None


def _get_glossary() -> Dict[str, Dict[str, str]]:
    """Get cached legal glossary."""
    global _legal_glossary
    if _legal_glossary is None:
        _legal_glossary = _load_legal_glossary()
    return _legal_glossary


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Translate a single text string from source to target language.

    Parameters
    ----------
    text : str
        Text to translate.
    source_lang : str
        Source language code (e.g., "en", "es").
    target_lang : str
        Target language code (e.g., "en", "es").

    Returns
    -------
    str
        Translated text with legal glossary applied.
    """
    if source_lang == target_lang:
        return text

    if target_lang == "en":
        # No translation needed if source is English
        if source_lang == "en":
            return text

    translator = _get_translator()
    if not translator:
        logger.warning("DeepL translator not available, returning original text")
        return text

    try:
        result = translator.translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        translated = result.text

        # Apply legal glossary replacements
        translated = _apply_legal_glossary(translated, target_lang)

        return translated

    except Exception as e:
        logger.error("DeepL translation failed: %s", e)
        return text  # Return original on failure


def translate_batch(
    texts: List[str],
    source_lang: str,
    target_lang: str,
) -> List[str]:
    """
    Translate multiple texts in a single API call.

    Parameters
    ----------
    texts : List[str]
        List of texts to translate.
    source_lang : str
        Source language code.
    target_lang : str
        Target language code.

    Returns
    -------
    List[str]
        List of translated texts.
    """
    if source_lang == target_lang:
        return texts

    translator = _get_translator()
    if not translator:
        logger.warning("DeepL translator not available, returning original texts")
        return texts

    try:
        results = translator.translate_text(
            texts,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        translated = [r.text for r in results]

        # Apply legal glossary to each translation
        glossary = _get_glossary()
        if glossary and target_lang in glossary:
            translated = [_apply_legal_glossary(t, target_lang) for t in translated]

        return translated

    except Exception as e:
        logger.error("DeepL batch translation failed: %s", e)
        return texts  # Return originals on failure


def _apply_legal_glossary(text: str, target_lang: str) -> str:
    """
    Apply legal glossary replacements to translated text.

    Parameters
    ----------
    text : str
        Translated text.
    target_lang : str
        Target language code.

    Returns
    -------
    str
        Text with glossary terms replaced.
    """
    glossary = _get_glossary()
    if not glossary or target_lang not in glossary:
        return text

    result = text
    for term_data in glossary.get(target_lang, []):
        if "original" in term_data and "translation" in term_data:
            result = result.replace(
                term_data["original"],
                term_data["translation"],
            )

    return result
