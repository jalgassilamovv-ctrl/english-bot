"""
Простая система интервального повторения (упрощённый вариант SM-2).
Каждое слово проходит через возрастающие интервалы повторения:
1 день -> 3 дня -> 7 дней -> 16 дней -> 30 дней -> 60 дней (дальше считается "выученным").
Если пользователь ответил неправильно — слово возвращается на первый интервал.
"""
from datetime import date, timedelta

INTERVALS_DAYS = [1, 3, 7, 16, 30, 60]


def initial_state():
    """Состояние для только что добавленного слова."""
    return {
        "interval_index": 0,
        "next_review_date": date.today().isoformat(),
        "status": "new",
    }


def next_state(interval_index: int, correct: bool):
    """
    Возвращает новое (interval_index, next_review_date, status) после ответа.
    """
    if correct:
        new_index = min(interval_index + 1, len(INTERVALS_DAYS) - 1)
        status = "known" if new_index == len(INTERVALS_DAYS) - 1 else "learning"
    else:
        new_index = 0
        status = "learning"

    days = INTERVALS_DAYS[new_index]
    next_date = date.today() + timedelta(days=days)
    return new_index, next_date.isoformat(), status
