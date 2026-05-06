from deep_translator import GoogleTranslator


def translate_to_english(
    text: str,
    source_lang: str
) -> str:
    if source_lang == "en":
        return text

    return GoogleTranslator(
        source=source_lang,
        target="en"
    ).translate(text)


def translate_from_english(
    text: str,
    target_lang: str
) -> str:
    if target_lang == "en":
        return text

    return GoogleTranslator(
        source="en",
        target=target_lang
    ).translate(text)