"""
Конфигурация бота. Все секреты (токены) читаются из переменных окружения,
чтобы их не хранить в коде. Смотри README.md — там объяснено, как задать
переменные окружения на Railway/Render или локально.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Обязательное ---
# Токен бота, который выдаёт @BotFather в Telegram (см. README, шаг 1).
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- Настройки обучения ---
# Сколько новых слов присылать в день (можно менять под себя).
NEW_WORDS_PER_DAY = int(os.environ.get("NEW_WORDS_PER_DAY", "15"))  # максимум 15

# Часовой пояс пользователя (Asia/Qyzylorda = UTC+5)
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Qyzylorda")

# Время утренней рассылки (новые слова) и вечерней (повтор + small talk)
MORNING_HOUR = int(os.environ.get("MORNING_HOUR", "8"))
MORNING_MINUTE = int(os.environ.get("MORNING_MINUTE", "0"))
EVENING_HOUR = int(os.environ.get("EVENING_HOUR", "19"))
EVENING_MINUTE = int(os.environ.get("EVENING_MINUTE", "30"))

# Соотношение технических/общих слов в ежедневной подборке (0.35 = 35% техники,
# 65% общей лексики и small talk — больше разговорной практики).
TECHNICAL_SHARE = float(os.environ.get("TECHNICAL_SHARE", "0.35"))

# Пауза между отправкой отдельных слов внутри одной утренней рассылки
# (секунды). Нужна, чтобы не упереться в лимиты Telegram при отправке
# 15 сообщений с голосом и картинкой подряд.
WORD_SEND_DELAY_SECONDS = float(os.environ.get("WORD_SEND_DELAY_SECONDS", "1.2"))

# --- Пути к данным ---
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "bot_data.sqlite3"
WORDS_GENERAL_PATH = DATA_DIR / "words_general.json"
WORDS_TECHNICAL_PATH = DATA_DIR / "words_technical.json"
PROMPTS_PATH = DATA_DIR / "conversation_prompts.json"

# --- Голосовой модуль ---
# Бесплатный режим (по умолчанию): распознавание речи через Google Web Speech
# API (бесплатно, без ключа, но требует интернет и не подходит для очень
# длинных записей) + озвучка ответов через gTTS (тоже бесплатно, без ключа).
#
# Если в будущем захочешь более умный "живой" диалог (не по сценариям),
# можно подключить платный LLM (OpenAI/Anthropic) — тогда впиши ключ ниже,
# и в utils/ai_brain.py включится "умный" режим автоматически.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # пусто = бесплатный режим

VOICE_LANG = "en-US"       # язык распознавания речи пользователя
TTS_LANG = "en"            # язык озвучки ответов бота

# Публичный бесплатный сервер LanguageTool для проверки грамматики.
# У него есть лимиты по частоте запросов — для одного пользователя достаточно.
LANGUAGETOOL_URL = os.environ.get(
    "LANGUAGETOOL_URL", "https://api.languagetool.org/v2/check"
)

# --- Картинки-иллюстрации к словам ---
# Бесплатный режим (по умолчанию): генерация через публичный сервис
# Pollinations.ai (бесплатно, без ключа и регистрации). Это сторонний
# бесплатный сервис "как есть" — иногда может быть медленным или временно
# недоступным, поэтому бот просто пропускает картинку, если она не пришла
# за отведённое время, и слово всё равно приходит текстом и голосом.
ENABLE_WORD_IMAGES = os.environ.get("ENABLE_WORD_IMAGES", "true").lower() != "false"
IMAGE_GENERATION_URL = os.environ.get(
    "IMAGE_GENERATION_URL", "https://image.pollinations.ai/prompt"
)
IMAGE_TIMEOUT_SECONDS = float(os.environ.get("IMAGE_TIMEOUT_SECONDS", "20"))
