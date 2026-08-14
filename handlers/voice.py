"""
Обработка голосовых сообщений: распознавание речи + маршрутизация
(ответ в рамках /talk, либо свободная практика) + команда /pronounce
для озвучки любого слова или фразы.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers import smalltalk
from utils import stt, tts

logger = logging.getLogger(__name__)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    if voice is None:
        return

    processing_msg = await update.message.reply_text("🎧 Слушаю...")

    try:
        file = await context.bot.get_file(voice.file_id)
        ogg_bytes = bytes(await file.download_as_bytearray())
        text = stt.transcribe_ogg_bytes(ogg_bytes)
    except ValueError as e:
        await processing_msg.edit_text(str(e))
        return
    except Exception:
        logger.exception("Ошибка распознавания речи")
        await processing_msg.edit_text(
            "Не получилось обработать голосовое сообщение. Попробуй ещё раз."
        )
        return

    await processing_msg.delete()

    if smalltalk.TALK_STATE_KEY in context.user_data:
        await smalltalk.process_talk_reply(update, context, text)
    else:
        await update.message.reply_text(
            f"📝 Я услышал: \"{text}\"\n\n"
            "Хочешь потренироваться по теме? Напиши /talk — я дам тему для разговора "
            "и разберу твою речь подробно."
        )


async def cmd_pronounce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Напиши слово или фразу после команды, например:\n/pronounce root cause analysis"
        )
        return
    phrase = " ".join(context.args)
    try:
        audio = tts.synthesize_to_ogg(phrase)
        await update.message.reply_voice(audio, caption=f"🔊 {phrase}")
    except Exception:
        logger.exception("Ошибка синтеза речи")
        await update.message.reply_text("Не получилось озвучить фразу, попробуй ещё раз позже.")
