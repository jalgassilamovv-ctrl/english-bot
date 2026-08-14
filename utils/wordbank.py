"""
Загрузка словарных баз и подбор ежедневной порции новых слов
(микс общих слов + технической лексики по инженерии/производству).
"""
import json
import random

import config

_general = None
_technical = None


def _load():
    global _general, _technical
    if _general is None:
        with open(config.WORDS_GENERAL_PATH, encoding="utf-8") as f:
            _general = json.load(f)
            for w in _general:
                w["_source"] = "general"
    if _technical is None:
        with open(config.WORDS_TECHNICAL_PATH, encoding="utf-8") as f:
            _technical = json.load(f)
            for w in _technical:
                w["_source"] = "technical"
    return _general, _technical


def all_words():
    g, t = _load()
    return g + t


def get_word_by_id(word_id: str):
    for w in all_words():
        if w["id"] == word_id:
            return w
    return None


def pick_daily_words(known_ids: set, count: int, technical_share: float):
    """Выбирает `count` новых слов, которых ещё нет у пользователя,
    смешивая технические и общие в пропорции technical_share."""
    general, technical = _load()

    def unseen(pool):
        return [w for w in pool if w["id"] not in known_ids]

    tech_pool = unseen(technical)
    gen_pool = unseen(general)

    tech_count = round(count * technical_share)
    gen_count = count - tech_count

    random.shuffle(tech_pool)
    random.shuffle(gen_pool)

    chosen = tech_pool[:tech_count] + gen_pool[:gen_count]

    # Если один словарь исчерпан — добираем из другого, чтобы всегда
    # присылать полную порцию, пока в базе остаются неизученные слова.
    remaining_needed = count - len(chosen)
    if remaining_needed > 0:
        leftovers = [w for w in (tech_pool + gen_pool) if w not in chosen]
        chosen += leftovers[:remaining_needed]

    random.shuffle(chosen)
    return chosen
