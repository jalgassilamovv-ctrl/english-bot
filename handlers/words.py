"""
Ежедневные слова: подбор, форматирование, отправка (утренняя рассылка и /today).
"""
import logging
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

import config
import db
from utils import wordbank, tts

logger = logging.getLogger(__name__)


def format_word(w: dict) -> str:
    tag = "🔧" if w["_source"] == "technical" else "💬"
    return (
        f"{tag} <b>{w['word']}</b> <i>({w['pos']})</i> — {w['ru']}\n"
        f"   {w['definition_en']}\n"
        f"   <i>\"{w['example_en']}\"</i>"
    )


def chunk_words(words: list, size: int = 9):
    for i in range(0, len(words), size):
        yield words[i : i + size]


async def send_daily_words(bot, chat_id: int, prepend: str = None):
    """Подбирает новую порцию слов, сохраняет в БД и отправляет пользователю."""
    known_ids = db.get_known_word_ids(chat_id)
    words = wordbank.pick_daily_words(known_ids, config.NEW_WORDS_PER_DAY, config.TECHNICAL_SHARE)

    if not words:
        await bot.send_message(
            chat_id,
            "🎉 Ты изучил все слова из моей базы! Напиши мне, и я подскажу, "
            "как расширить словарную базу дальше.",
        )
        return

    db.add_words_to_progress(chat_id, words)
    db.log_new_words_sent(chat_id, len(words))
    db.promote_new_to_learning(chat_id, [w["id"] for w in words])

    header = f"📚 <b>Твои {len(words)} новых слов на сегодня</b>\n(🔧 техническое · 💬 общее)\n"
    if prepend:
        header = prepend + "\n\n" + header

    chunks = list(chunk_words(words, 9))
    first = True
    for chunk in chunks:
        text = (header if first else "") + "\n\n".join(format_word(w) for w in chunk)
        await bot.send_message(chat_id, text, parse_mode="HTML")
        first = False

    await bot.send_message(
        chat_id,
        "Совет: пройди /quiz сегодня вечером, чтобы слова закрепились в памяти. "
        "Хочешь услышать произношение — напиши /pronounce и слово.",
    )

    # Голосовая озвучка примеров — не критично, если не получится, просто пропускаем.
    try:
        sample = words[: min(len(words), 12)]
        speech_text = ". ".join(w["example_en"] for w in sample)
        audio = tts.synthesize_to_ogg(speech_text)
        await bot.send_voice(chat_id, audio, caption="🔊 Послушай примеры сегодняшних слов")
    except Exception:
        logger.exception("TTS для ежедневных слов не сработал (это не критично)")


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.touch_activity(chat_id)
    today_ids = db.get_words_added_on(chat_id, date.today().isoformat())
    if not today_ids:
        await update.message.reply_text(
            "На сегодня слова ещё не были присланы — отправляю подборку прямо сейчас!"
        )
        await send_daily_words(context.bot, chat_id)
        return
    words = [wordbank.get_word_by_id(wid) for wid in today_ids]
    words = [w for w in words if w]
    header = f"📚 <b>Слова, которые ты уже получил сегодня ({len(words)})</b>\n"
    chunks = list(chunk_words(words, 9))
    first = True
    for chunk in chunks:
        text = (header if first else "") + "\n\n".join(format_word(w) for w in chunk)
        await update.message.reply_text(text, parse_mode="HTML")
        first = False
