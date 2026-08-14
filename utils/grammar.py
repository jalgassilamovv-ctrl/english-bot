"""
Проверка грамматики через бесплатный публичный сервер LanguageTool
(без API-ключа, есть ограничение по частоте запросов — для одного
пользователя, занимающегося пару раз в день, этого достаточно).
Если сервис недоступен — просто пропускаем проверку, не ломая бота.
"""
import requests

import config


def check_grammar(text: str, max_suggestions: int = 3):
    """Возвращает список коротких понятных подсказок на русском."""
    try:
        response = requests.post(
            config.LANGUAGETOOL_URL,
            data={"text": text, "language": "en-US"},
            timeout=8,
        )
        response.raise_for_status()
        matches = response.json().get("matches", [])
    except Exception:
        return []

    tips = []
    for m in matches[:max_suggestions]:
        bad_part = text[m["offset"] : m["offset"] + m["length"]]
        replacements = [r["value"] for r in m.get("replacements", [])[:2]]
        message = m.get("message", "")
        if replacements:
            tip = f'"{bad_part}" → лучше: {", ".join(replacements)} ({message})'
        else:
            tip = f'"{bad_part}": {message}'
        tips.append(tip)
    return tips
