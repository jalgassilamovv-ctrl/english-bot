from telegram import Update
from telegram.ext import ContextTypes

import db
from handlers.words import send_daily_words

WELCOME = """\
Привет, {name}! 👋 Я твой личный помощник для изучения английского.

Вот что я умею:
📚 Каждый день присылаю 25-30 новых слов — общих и технических (инженерия/производство)
🔁 Слежу за повторением по интервалам, чтобы слова не забывались (/quiz)
🎙 Устраиваю голосовую практику и small talk — присылай мне голосовые сообщения! (/talk)
🔊 Озвучиваю произношение любого слова (/pronounce word)
📈 Слежу за streak (днями подряд) и мотивирую не бросать

Напоминания приходят два раза в день: утром — новые слова, вечером — повторение и разговорная практика.

Команды:
/today — сегодняшние слова
/quiz — квиз на повторение
/talk — начать разговорную практику (ответь голосом!)
/pronounce слово — услышать произношение
/stats — твой прогресс
/help — это сообщение

Погнали! Вот твоя первая подборка слов 👇
"""

HELP = """\
Команды:
/today — сегодняшние слова
/quiz — квиз на повторение слов
/talk — разговорная практика (ответь голосовым сообщением)
/pronounce слово или фраза — услышать произношение
/stats — статистика и streak
/help — список команд

Просто отправь мне голосовое сообщение в любой момент — я расшифрую его \
и подскажу, что улучшить в грамматике.
"""


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name or "друг"
    db.get_or_create_user(chat_id, name)
    db.touch_activity(chat_id)

    await update.message.reply_text(WELCOME.format(name=name))
    await send_daily_words(context.bot, chat_id)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)
