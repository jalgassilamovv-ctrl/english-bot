"""
Small talk и разговорная практика (включая технический английский по
инженерии/производству). Пользователь получает тему, отвечает голосовым
сообщением, бот распознаёт речь, мягко проверяет грамматику и продолжает
разговор follow-up вопросом — так тренируется именно свободная речь и
способность формулировать мысли, а не просто перевод отдельных слов.
"""
import json
import random

from telegram import Update
from telegram.ext import ContextTypes

import config
import db
from utils import ai_brain, grammar, tts

TALK_STATE_KEY = "talk_prompt"
TALK_ROUND_KEY = "talk_round"
MAX_ROUNDS = 3

with open(config.PROMPTS_PATH, encoding="utf-8") as f:
    PROMPTS = json.load(f)


def _pick_prompt(category: str = None):
    category = category or random.choice(["general", "technical"])
    return category, random.choice(PROMPTS[category])


async def cmd_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.touch_activity(chat_id)

    category, prompt = _pick_prompt()
    context.user_data[TALK_STATE_KEY] = prompt
    context.user_data[TALK_ROUND_KEY] = 1

    label = "🔧 Технический английский" if category == "technical" else "💬 Small talk"
    text = (
        f"{label}\n\n"
        f"<b>RU:</b> {prompt['prompt_ru']}\n"
        f"<b>EN:</b> {prompt['prompt_en']}\n\n"
        "🎙 Ответь голосовым сообщением на английском — можно 3-6 предложений, "
        "не бойся ошибок, это практика!"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def start_talk_for_chat(bot, chat_id: int, category: str = None, note: str = None):
    """Используется планировщиком для вечерней рассылки (без Update)."""
    cat, prompt = _pick_prompt(category)
    label = "🔧 Технический английский" if cat == "technical" else "💬 Small talk"
    text = (
        f"{label}\n\n"
        f"<b>RU:</b> {prompt['prompt_ru']}\n"
        f"<b>EN:</b> {prompt['prompt_en']}\n\n"
        "🎙 Ответь голосовым сообщением на английском, когда будет удобно."
    )
    if note:
        text = note + "\n\n" + text
    await bot.send_message(chat_id, text, parse_mode="HTML")
    return prompt


async def process_talk_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, transcribed_text: str):
    chat_id = update.effective_chat.id
    prompt = context.user_data.get(TALK_STATE_KEY)

    await update.message.reply_text(f"📝 Я услышал: \"{transcribed_text}\"")

    tips = grammar.check_grammar(transcribed_text)
    if tips:
        tips_text = "\n".join(f"• {t}" for t in tips)
        await update.message.reply_text(f"🔍 Небольшие подсказки по грамматике:\n{tips_text}")
    else:
        await update.message.reply_text("👍 Грамматика выглядит хорошо!")

    encouragement = ai_brain.pick_encouragement(PROMPTS)
    round_num = context.user_data.get(TALK_ROUND_KEY, 1)

    db.log_talk_done(chat_id)

    if prompt and round_num < MAX_ROUNDS:
        followup = ai_brain.pick_followup(prompt)
        context.user_data[TALK_ROUND_KEY] = round_num + 1
        await update.message.reply_text(f"{encouragement}\n\n❓ {followup}")
        try:
            audio = tts.synthesize_to_ogg(followup)
            await update.message.reply_voice(audio)
        except Exception:
            pass
    else:
        context.user_data.pop(TALK_STATE_KEY, None)
        context.user_data.pop(TALK_ROUND_KEY, None)
        await update.message.reply_text(
            f"{encouragement}\n\nОтличный разговор! Напиши /talk, когда захочешь "
            "потренироваться ещё раз, или /quiz — закрепить сегодняшние слова."
        )
