"""
Озвучка текста (Text-to-Speech) БЕСПЛАТНЫМ способом через gTTS
(использует голос Google Translate — без API-ключа).
Результат конвертируется в .ogg/Opus, чтобы Telegram показывал его
как обычное голосовое сообщение.
"""
import io

from gtts import gTTS
from pydub import AudioSegment

import config


def synthesize_to_ogg(text: str) -> bytes:
    mp3_io = io.BytesIO()
    tts = gTTS(text=text, lang=config.TTS_LANG, slow=False)
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)

    audio = AudioSegment.from_file(mp3_io, format="mp3")
    ogg_io = io.BytesIO()
    audio.export(ogg_io, format="ogg", codec="libopus")
    ogg_io.seek(0)
    return ogg_io.read()
