"""
Распознавание речи (Speech-to-Text) БЕСПЛАТНЫМ способом:
через встроенный в библиотеку SpeechRecognition бесплатный доступ
к Google Web Speech API (не требует ключа, но требует интернет
и не подходит для очень длинных записей — оптимально до ~1 минуты).

Telegram присылает голосовые сообщения в формате .ogg (Opus).
Сначала конвертируем в .wav (нужен установленный ffmpeg в системе),
затем распознаём.
"""
import io

import speech_recognition as sr
from pydub import AudioSegment

import config


def transcribe_ogg_bytes(ogg_bytes: bytes) -> str:
    """Возвращает распознанный текст или бросает ValueError, если не удалось."""
    audio = AudioSegment.from_file(io.BytesIO(ogg_bytes), format="ogg")
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language=config.VOICE_LANG)
        return text
    except sr.UnknownValueError:
        raise ValueError(
            "Не удалось распознать речь. Попробуй говорить чуть медленнее и ближе к микрофону."
        )
    except sr.RequestError as e:
        raise ValueError(f"Сервис распознавания речи временно недоступен ({e}).")
