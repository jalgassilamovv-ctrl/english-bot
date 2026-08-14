"""
"Мозг" разговорного модуля.

По умолчанию (бесплатный режим, OPENAI_API_KEY не задан) бот ведёт
разговор по заранее подготовленным сценариям small talk / технического
английского: даёт тему, слушает голосовой ответ, проверяет грамматику
через LanguageTool, хвалит/подсказывает и задаёт один из готовых
follow-up вопросов. Это не "живой" ИИ-диалог, а структурированная
практика, но она бесплатна и работает без ограничений.

Если в будущем добавить OPENAI_API_KEY в переменные окружения — бот
автоматически начнёт использовать GPT для более естественного,
свободного диалога (см. функцию generate_smart_reply). Это опционально
и не обязательно для работы бота.
"""
import random

import config


def has_smart_mode() -> bool:
    return bool(config.OPENAI_API_KEY)


def generate_smart_reply(user_text: str, context: dict) -> str:
    """Используется только если задан OPENAI_API_KEY. Импортируем openai
    здесь же, чтобы библиотека не была обязательной для бесплатного режима."""
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    system_prompt = (
        "You are a friendly, encouraging English tutor helping a B1-level "
        "engineer practice speaking and technical English. Reply in English, "
        "keep it short (2-4 sentences), gently correct major mistakes, and "
        "always end with one follow-up question to keep the conversation going."
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=200,
    )
    return completion.choices[0].message.content.strip()


def pick_followup(prompt_obj: dict) -> str:
    return random.choice(prompt_obj["followups"])


def pick_encouragement(prompts_data: dict) -> str:
    return random.choice(prompts_data["encouragement"])


def pick_reengagement(prompts_data: dict) -> str:
    return random.choice(prompts_data["reengagement"])
