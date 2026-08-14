from telegram import Update
from telegram.ext import ContextTypes

import db


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    stats = db.get_stats(chat_id)

    fire = "🔥" * min(stats["streak"], 10) if stats["streak"] else "—"
    text = (
        "📈 <b>Твой прогресс</b>\n\n"
        f"Дней подряд: {stats['streak']} {fire}\n"
        f"Лучшая серия: {stats['longest_streak']}\n"
        f"Слов в изучении: {stats['total_words']}\n"
        f"Слов выучено насовсем: {stats['known_words']}\n\n"
        "Так держать! Продолжай ежедневную практику 💪"
    )
    await update.message.reply_text(text, parse_mode="HTML")
