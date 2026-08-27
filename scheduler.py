"""
Планировщик ежедневных напоминаний: утро — новые слова, вечер — повторение
+ разговорная практика. Использует встроенный JobQueue библиотеки
python-telegram-bot (нужен пакет python-telegram-bot[job-queue]).
"""
import datetime as dt
import logging
from zoneinfo import ZoneInfo

from telegram.ext import Application

import config
import db
from handlers.smalltalk import (
    TALK_ROUND_KEY,
    TALK_STATE_KEY,
    TALK_USED_FOLLOWUPS_KEY,
    start_talk_for_chat,
)
from handlers.words import send_daily_words
from utils.ai_brain import pick_reengagement
import json

logger = logging.getLogger(__name__)

with open(config.PROMPTS_PATH, encoding="utf-8") as f:
    PROMPTS_DATA = json.load(f)

TZ = ZoneInfo(config.TIMEZONE)


async def morning_job(context):
    for chat_id in db.get_all_user_ids():
        try:
            gap = db.days_since_last_active(chat_id)
            note = pick_reengagement(PROMPTS_DATA) if gap and gap > 1 else None
            await send_daily_words(context.bot, chat_id, prepend=note)
        except Exception:
            logger.exception("Не удалось отправить утреннюю рассылку для %s", chat_id)


async def evening_job(context):
    for chat_id in db.get_all_user_ids():
        try:
            due = db.get_words_due_today(chat_id, limit=15)
            if due:
                await context.bot.send_message(
                    chat_id,
                    f"🌙 Вечернее напоминание! На повторение готово слов: {len(due)}.\n"
                    "Запусти /quiz, чтобы закрепить их.",
                )
            prompt = await start_talk_for_chat(context.bot, chat_id)
            # Важно: сохраняем состояние диалога в то же хранилище user_data,
            # которое использует обработчик голосовых сообщений, иначе бот не
            # поймёт, что голосовой ответ пользователя относится к этой теме.
            # Работает для личного чата один-на-один с ботом, где chat_id == user_id.
            user_data = context.application.user_data[chat_id]
            user_data[TALK_STATE_KEY] = prompt
            user_data[TALK_ROUND_KEY] = 1
            user_data[TALK_USED_FOLLOWUPS_KEY] = []
        except Exception:
            logger.exception("Не удалось отправить вечернюю рассылку для %s", chat_id)


def register_jobs(application: Application):
    jq = application.job_queue
    jq.run_daily(
        morning_job,
        time=dt.time(hour=config.MORNING_HOUR, minute=config.MORNING_MINUTE, tzinfo=TZ),
        name="morning_words",
    )
    jq.run_daily(
        evening_job,
        time=dt.time(hour=config.EVENING_HOUR, minute=config.EVENING_MINUTE, tzinfo=TZ),
        name="evening_review",
    )
