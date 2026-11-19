"""Алгоритм подбора совпадений «потерял — нашёл».

Расчёт оценки (score_pair) — чистая функция без обращения к базе,
её можно тестировать отдельно. find_matches_for и функции показа
работают с переданным соединением sqlite3.
"""
import re

# ----------------------------- Константы -----------------------------
# Сумма весов равна 100. Значения подобраны скриптом tune_matching.py,
# подробности в docs/matching-tuning.md.
W_CATEGORY = 30   # совпала категория
W_PLACE = 25      # максимум за место (то же место)
W_TIME = 20       # максимум за время (разница 1 день)
W_TEXT = 15       # максимум за текст
W_PHOTO = 10      # фото у обоих объявлений

PLACE_SAME = 25       # то же место
PLACE_NEIGHBOR = 10   # соседнее место

# (разница в днях не больше N, баллы) — первое подходящее правило
TIME_STEPS = ((1, 20), (3, 15), (7, 10), (14, 5))

MIN_SCORE = 60  # порог, ниже которого пара не сохраняется

# Простые стоп-слова, не несущие смысла для сравнения
STOP_WORDS = {
    "и", "в", "на", "с", "у", "по", "для", "это", "как",
    "мой", "моя", "моё", "был", "была", "найден", "найдена",
    "потерял", "потеряла", "нашёл", "нашла",
}

WORD_RE = re.compile(r"\w+", re.UNICODE)
STEM_LEN = 5  # сравниваем первые 5 символов слова — устойчивость к окончаниям


# --------------------------- Чистая часть ---------------------------

def extract_words(text):
    """Множество «основ» слов из текста: нижний регистр, буквы и цифры,
    без слов короче 3 символов и стоп-слов, сравнение по первым 5 символам."""
    stems = set()
    if not text:
        return stems
    for word in WORD_RE.findall(text.lower()):
        if len(word) < 3 or word in STOP_WORDS:
            continue
        stems.add(word[:STEM_LEN])
    return stems


def text_part(lost, found):
    """Текстовая часть оценки: W_TEXT * доля общих слов.

    Возвращает (баллы, список причин). Если слов нет у одного из
    объявлений — (0, []).
    """
    lost_words = extract_words((lost.get("title") or "") + " " + (lost.get("description") or ""))
    found_words = extract_words((found.get("title") or "") + " " + (found.get("description") or ""))
    if not lost_words or not found_words:
        return 0, []

    common = lost_words & found_words
    if not common:
        return 0, []

    share = len(common) / min(len(lost_words), len(found_words))
    score = round(W_TEXT * share)

    # для причины показываем сами слова, а не укороченные основы
    lost_all = WORD_RE.findall(((lost.get("title") or "") + " " + (lost.get("description") or "")).lower())
    examples = []
    for word in lost_all:
        if word[:STEM_LEN] in common and word not in examples:
            examples.append(word)
    reason = "общие слова: " + ", ".join(examples[:5])
    return score, [reason]


def _parse_date(value):
    from datetime import date
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def score_pair(lost, found, neighbor_pairs):
    """Оценка пары «потерял/нашёл». Возвращает (баллы 0-100, причины)
    или None, если пара отбрасывается.

    Отбрасывается: другая категория, дата находки раньше даты потери,
    некорректные даты.
    """
    if lost.get("category_id") != found.get("category_id"):
        return None

    lost_date = _parse_date(lost.get("date"))
    found_date = _parse_date(found.get("date"))
    if lost_date is None or found_date is None:
        return None
    if found_date < lost_date:
        return None

    reasons = ["совпала категория"]
    score = W_CATEGORY

    # Место
    if lost.get("place_id") == found.get("place_id"):
        score += PLACE_SAME
        reasons.append("то же место")
    elif (lost.get("place_id"), found.get("place_id")) in neighbor_pairs:
        score += PLACE_NEIGHBOR
        reasons.append("соседнее место")

    # Время
    diff = (found_date - lost_date).days
    for limit, points in TIME_STEPS:
        if diff <= limit:
            score += points
            reasons.append(f"разница в {diff} дн.")
            break

    # Текст
    text_score, text_reasons = text_part(lost, found)
    score += text_score
    reasons.extend(text_reasons)

    # Фото (заготовка под будущее сравнение изображений)
    if lost.get("photo") and found.get("photo"):
        score += W_PHOTO
        reasons.append("есть фото у обоих")

    return min(score, 100), reasons


# --------------------------- Работа с базой ---------------------------

def load_neighbor_pairs(conn):
    """Множество пар соседних мест (place_id, neighbor_id) — одним запросом."""
    rows = conn.execute("SELECT place_id, neighbor_id FROM place_neighbors").fetchall()
    return {(row["place_id"], row["neighbor_id"]) for row in rows}


def find_matches_for(conn, item_id):
    """Подбор совпадений для объявления.

    Кандидаты — активные объявления противоположного типа, той же
    категории, другого автора. Пары с оценкой не ниже MIN_SCORE
    сохраняются через INSERT OR IGNORE (правильный порядок
    lost/found, существующие пары не пересоздаются и не меняются).
    Возвращает число добавленных пар.
    """
    item_row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item_row is None:
        return 0
    item = dict(item_row)
    neighbor_pairs = load_neighbor_pairs(conn)

    opposite_type = "found" if item["type"] == "lost" else "lost"
    candidates = conn.execute(
        "SELECT * FROM items "
        "WHERE status = 'active' AND type = ? AND category_id = ? "
        "AND user_id != ? AND id != ?",
        (opposite_type, item["category_id"], item["user_id"], item_id),
    ).fetchall()

    added = 0
    for candidate_row in candidates:
        candidate = dict(candidate_row)
        # score_pair(потерянное, найденное) — порядок фиксирован
        if item["type"] == "lost":
            result = score_pair(item, candidate, neighbor_pairs)
        else:
            result = score_pair(candidate, item, neighbor_pairs)
        if result is None:
            continue
        score, _reasons = result
        if score < MIN_SCORE:
            continue
        if item["type"] == "lost":
            lost_item_id, found_item_id = item["id"], candidate["id"]
        else:
            lost_item_id, found_item_id = candidate["id"], item["id"]
        cur = conn.execute(
            "INSERT OR IGNORE INTO matches (lost_item_id, found_item_id, score) "
            "VALUES (?, ?, ?)",
            (lost_item_id, found_item_id, score),
        )
        added += cur.rowcount
    return added


def load_matches_for_item(conn, item):
    """Совпадения объявления для показа (только пока оно активно).

    Возвращает список словарей: match, other (объявление другой стороны),
    contact (контакт другой стороны), reasons (пересчёт через score_pair).
    Сортировка по убыванию оценки.
    """
    if item["status"] != "active":
        return []
    if item["type"] == "lost":
        sql = (
            "SELECT matches.id AS match_id, matches.score AS score, "
            "matches.status AS status, items_other.*, "
            "places.name AS place_name, users.contact AS other_contact "
            "FROM matches "
            "JOIN items AS items_other ON items_other.id = matches.found_item_id "
            "JOIN places ON places.id = items_other.place_id "
            "JOIN users ON users.id = items_other.user_id "
            "WHERE matches.lost_item_id = ? "
            "AND matches.status IN ('new', 'confirmed') "
            "AND items_other.status = 'active' "
            "ORDER BY matches.score DESC"
        )
    else:
        sql = (
            "SELECT matches.id AS match_id, matches.score AS score, "
            "matches.status AS status, items_other.*, "
            "places.name AS place_name, users.contact AS other_contact "
            "FROM matches "
            "JOIN items AS items_other ON items_other.id = matches.lost_item_id "
            "JOIN places ON places.id = items_other.place_id "
            "JOIN users ON users.id = items_other.user_id "
            "WHERE matches.found_item_id = ? "
            "AND matches.status IN ('new', 'confirmed') "
            "AND items_other.status = 'active' "
            "ORDER BY matches.score DESC"
        )
    rows = conn.execute(sql, (item["id"],)).fetchall()
    if not rows:
        return []

    # для пересчёта причин нужны полные строки обоих объявлений и соседи
    neighbor_pairs = load_neighbor_pairs(conn)

    result = []
    for row in rows:
        other = conn.execute(
            "SELECT * FROM items WHERE id = ?", (row["id"],)
        ).fetchone()
        if other is None:
            continue
        if item["type"] == "lost":
            lost_row, found_row = dict(item), dict(other)
        else:
            lost_row, found_row = dict(other), dict(item)
        score_result = score_pair(lost_row, found_row, neighbor_pairs)
        reasons = score_result[1] if score_result else []
        result.append({
            "match_id": row["match_id"],
            "score": row["score"],
            "status": row["status"],
            "other": row,
            "contact": row["other_contact"],
            "reasons": reasons,
        })
    return result


def load_matches_for_user(conn, user_id):
    """Совпадения всех активных объявлений пользователя (для кабинета).

    Возвращает список (объявление, совпадения) по тем же правилам,
    что и на странице объявления.
    """
    items = conn.execute(
        "SELECT * FROM items WHERE user_id = ? AND status = 'active' ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    result = []
    for item in items:
        matches = load_matches_for_item(conn, item)
        if matches:
            result.append({"item": item, "matches": matches})
    return result
