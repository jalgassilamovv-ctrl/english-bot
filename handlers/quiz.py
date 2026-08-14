"""
Мини-квиз для закрепления слов: бот показывает английское слово,
пользователь пишет перевод или объяснение своими словами, бот проверяет
(нестрого — по совпадению ключевых слов) и обновляет интервал повторения.
"""
import difflib

from telegram import Update
from telegram.ext import ContextTypes

import db
from utils import wordbank

QUIZ_QUEUE_KEY = "quiz_queue"
QUIZ_CURRENT_KEY = "quiz_current_word_id"


def _is_answer_close_enough(user_answer: str, correct_ru: str) -> bool:
    user_answer = user_answer.strip().lower()
    if not user_answer:
        return False
    # correct_ru может содержать несколько вариантов через запятую
    variants = [v.strip().lower() for v in correct_ru.split(",")]
    for variant in variants:
        if user_answer in variant or variant in user_answer:
            return True
        ratio = difflib.SequenceMatcher(None, user_answer, variant).ratio()
        if ratio > 0.6:
            return True
    return False


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.touch_activity(chat_id)

    due = db.get_words_due_today(chat_id, limit=15)
    if not due:
        await update.message.reply_text(
            "Сейчас нет слов, готовых для повторения 🙌 Загляни позже или "
            "используй /today, чтобы посмотреть слова этого дня."
        )
        return

    words = []
    for row in due:
        w = wordbank.get_word_by_id(row["word_id"])
        if w:
            words.append(w)

    context.user_data[QUIZ_QUEUE_KEY] = words
    await update.message.reply_text(
        f"🧠 Квиз! Слов на повторение: {len(words)}.\n"
        "Напиши перевод или объяснение каждого слова своими словами."
    )
    await _ask_next(update, context)


async def _ask_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    queue = context.user_data.get(QUIZ_QUEUE_KEY, [])
    if not queue:
        context.user_data.pop(QUIZ_CURRENT_KEY, None)
        stats = db.get_stats(update.effective_chat.id)
        await update.effective_chat.send_message(
            "✅ Квиз завершён! Отличная работа.\n"
            f"Выучено слов насовсем: {stats['known_words']} · "
            f"Дней подряд: {stats['streak']} 🔥"
        )
        return
    word = queue[0]
    context.user_data[QUIZ_CURRENT_KEY] = word["id"]
    await update.effective_chat.send_message(
        f"❓ Что значит слово: <b>{word['word']}</b>?", parse_mode="HTML"
    )


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Возвращает True, если сообщение было обработано как ответ квиза."""
    word_id = context.user_data.get(QUIZ_CURRENT_KEY)
    if not word_id:
        return False

    chat_id = update.effective_chat.id
    word = wordbank.get_word_by_id(word_id)
    user_answer = update.message.text or ""

    correct = _is_answer_close_enough(user_answer, word["ru"]) if word else False
    db.mark_review_result(chat_id, word_id, correct)

    if correct:
        await update.message.reply_text("✅ Верно!")
    else:
        await update.message.reply_text(
            f"❌ Правильный ответ: <b>{word['ru']}</b>\n<i>{word['example_en']}</i>",
            parse_mode="HTML",
        )

    queue = context.user_data.get(QUIZ_QUEUE_KEY, [])
    if queue:
        queue.pop(0)
    context.user_data[QUIZ_QUEUE_KEY] = queue
    context.user_data.pop(QUIZ_CURRENT_KEY, None)
    await _ask_next(update, context)
    return True
