"""
Работа с базой данных (SQLite, один файл bot_data.sqlite3).
Хранит: пользователей, прогресс по каждому слову, историю дней (streak).
"""
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta

import config
from utils.spaced_repetition import initial_state, next_state

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    level TEXT DEFAULT 'B1',
    streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_active_date TEXT,
    total_words_learned INTEGER DEFAULT 0,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS word_progress (
    chat_id INTEGER,
    word_id TEXT,
    source TEXT,
    status TEXT DEFAULT 'new',
    interval_index INTEGER DEFAULT 0,
    next_review_date TEXT,
    times_seen INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    added_date TEXT,
    PRIMARY KEY (chat_id, word_id)
);

CREATE TABLE IF NOT EXISTS daily_log (
    chat_id INTEGER,
    log_date TEXT,
    new_words_sent INTEGER DEFAULT 0,
    quiz_done INTEGER DEFAULT 0,
    talk_done INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, log_date)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def get_or_create_user(chat_id: int, name: str = ""):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO users (chat_id, name, created_at, last_active_date) "
            "VALUES (?, ?, ?, ?)",
            (chat_id, name, datetime.utcnow().isoformat(), ""),
        )
        row = conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row)


def get_user(chat_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_user_ids():
    with get_conn() as conn:
        rows = conn.execute("SELECT chat_id FROM users").fetchall()
        return [r["chat_id"] for r in rows]


def days_since_last_active(chat_id: int) -> int:
    user = get_user(chat_id)
    if not user or not user["last_active_date"]:
        return 0
    last = date.fromisoformat(user["last_active_date"])
    return (date.today() - last).days


def touch_activity(chat_id: int):
    """Обновляет streak: если пользователь писал вчера — +1, если сегодня уже
    отмечен — не трогаем, если был перерыв — streak сбрасывается на 1."""
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_active_date, streak, longest_streak FROM users WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        if row is None:
            return
        last_active, streak, longest = row["last_active_date"], row["streak"], row["longest_streak"]
        if last_active == today:
            return  # уже отмечено сегодня
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if last_active == yesterday:
            streak += 1
        else:
            streak = 1
        longest = max(longest, streak)
        conn.execute(
            "UPDATE users SET last_active_date = ?, streak = ?, longest_streak = ? "
            "WHERE chat_id = ?",
            (today, streak, longest, chat_id),
        )


def get_known_word_ids(chat_id: int) -> set:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT word_id FROM word_progress WHERE chat_id = ?", (chat_id,)
        ).fetchall()
        return {r["word_id"] for r in rows}


def add_words_to_progress(chat_id: int, words: list):
    """words: список dict с 'id' и '_source' ('general'/'technical')."""
    today = date.today().isoformat()
    with get_conn() as conn:
        for w in words:
            state = initial_state()
            conn.execute(
                "INSERT OR IGNORE INTO word_progress "
                "(chat_id, word_id, source, status, interval_index, next_review_date, added_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    chat_id,
                    w["id"],
                    w["_source"],
                    state["status"],
                    state["interval_index"],
                    state["next_review_date"],
                    today,
                ),
            )


def get_words_added_on(chat_id: int, iso_date: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT word_id FROM word_progress WHERE chat_id = ? AND added_date = ?",
            (chat_id, iso_date),
        ).fetchall()
        return [r["word_id"] for r in rows]


def get_words_due_today(chat_id: int, limit: int = 15) -> list:
    """Слова, интервал повторения которых наступил (<= сегодня)."""
    today = date.today().isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM word_progress WHERE chat_id = ? AND status != 'known' "
            "AND next_review_date <= ? ORDER BY next_review_date LIMIT ?",
            (chat_id, today, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_review_result(chat_id: int, word_id: str, correct: bool):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT interval_index, times_seen, times_correct FROM word_progress "
            "WHERE chat_id = ? AND word_id = ?",
            (chat_id, word_id),
        ).fetchone()
        if row is None:
            return
        new_index, next_date, status = next_state(row["interval_index"], correct)
        times_seen = row["times_seen"] + 1
        times_correct = row["times_correct"] + (1 if correct else 0)
        conn.execute(
            "UPDATE word_progress SET interval_index=?, next_review_date=?, status=?, "
            "times_seen=?, times_correct=? WHERE chat_id=? AND word_id=?",
            (new_index, next_date, status, times_seen, times_correct, chat_id, word_id),
        )
        if status == "known":
            conn.execute(
                "UPDATE users SET total_words_learned = total_words_learned + 1 WHERE chat_id = ?",
                (chat_id,),
            )


def promote_new_to_learning(chat_id: int, word_ids: list):
    """После того как новое слово показано утром, переводим его из 'new'
    в обычный цикл повторения, чтобы вечером оно попало в повторение."""
    with get_conn() as conn:
        for wid in word_ids:
            conn.execute(
                "UPDATE word_progress SET status = 'learning' WHERE chat_id = ? "
                "AND word_id = ? AND status = 'new'",
                (chat_id, wid),
            )


def log_new_words_sent(chat_id: int, count: int):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO daily_log (chat_id, log_date, new_words_sent) VALUES (?, ?, ?) "
            "ON CONFLICT(chat_id, log_date) DO UPDATE SET new_words_sent = new_words_sent + excluded.new_words_sent",
            (chat_id, today, count),
        )


def log_talk_done(chat_id: int):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO daily_log (chat_id, log_date, talk_done) VALUES (?, ?, 1) "
            "ON CONFLICT(chat_id, log_date) DO UPDATE SET talk_done = 1",
            (chat_id, today),
        )


def get_stats(chat_id: int):
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        total_words = conn.execute(
            "SELECT COUNT(*) c FROM word_progress WHERE chat_id = ?", (chat_id,)
        ).fetchone()["c"]
        known = conn.execute(
            "SELECT COUNT(*) c FROM word_progress WHERE chat_id = ? AND status = 'known'",
            (chat_id,),
        ).fetchone()["c"]
        return {
            "streak": user["streak"] if user else 0,
            "longest_streak": user["longest_streak"] if user else 0,
            "total_words": total_words,
            "known_words": known,
        }
