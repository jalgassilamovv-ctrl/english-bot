"""
Точка входа. Запуск: python bot.py
Перед запуском обязательно задай переменную окружения BOT_TOKEN
(см. README.md — как получить токен у @BotFather).
"""
import logging

try:
    from dotenv import load_dotenv

    load_dotenv()  # подхватывает переменные из файла .env, если он есть
except ImportError:
    pass

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import db
from handlers.quiz import cmd_quiz, handle_quiz_answer
from handlers.smalltalk import cmd_talk
from handlers.start import cmd_help, cmd_start
from handlers.stats import cmd_stats
from handlers.tips import cmd_tips
from handlers.voice import cmd_pronounce, handle_voice_message
from handlers.words import cmd_today
from scheduler import register_jobs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текстовые сообщения используются как ответы в квизе. Всё остальное —
    короткая подсказка, чтобы пользователь не терялся."""
    handled = await handle_quiz_answer(update, context)
    if handled:
        return
    await update.message.reply_text(
        "Я лучше понимаю голосовые сообщения и команды 🙂\n"
        "Попробуй /talk для разговорной практики, /quiz для повторения слов "
        "или /help — список всех команд."
    )


def main():
    if not config.BOT_TOKEN:
        raise SystemExit(
            "Не задан BOT_TOKEN. Установи переменную окружения BOT_TOKEN "
            "(см. README.md, шаг 1-2) и запусти снова."
        )

    db.init_db()

    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("quiz", cmd_quiz))
    application.add_handler(CommandHandler("talk", cmd_talk))
    application.add_handler(CommandHandler("pronounce", cmd_pronounce))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("tips", cmd_tips))

    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    register_jobs(application)

    logger.info("Бот запущен. Ожидание сообщений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
