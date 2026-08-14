"""
Совместимость со свежими версиями Python (3.13+), которые убрали из
стандартной библиотеки несколько старых модулей (audioop, aifc, chunk),
нужных библиотекам pydub и SpeechRecognition. В requirements.txt уже
подключены официальные бэкпорты (audioop-lts, standard-aifc,
standard-chunk) — их обычно достаточно.

Этот файл — дополнительная подстраховка на случай, если бэкпорт по
какой-то причине не установился: он подставляет пустую "заглушку" вместо
модуля, чтобы `import` в чужих библиотеках не падал и бот в принципе
запускался. Наш код использует только базовую конвертацию форматов через
ffmpeg (не сырые аудио-функции), поэтому заглушки не мешают основной
функциональности голосового модуля.

Импортировать этот файл нужно ДО `speech_recognition` и `pydub`.
"""
import sys
import types

for _mod_name in ("audioop", "aifc", "chunk", "sunau"):
    if _mod_name in sys.modules:
        continue
    try:
        __import__(_mod_name)
    except ModuleNotFoundError:
        sys.modules[_mod_name] = types.ModuleType(_mod_name)
