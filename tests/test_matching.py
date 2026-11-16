# -*- coding: utf-8 -*-
"""Тесты чистой функции score_pair и find_matches_for."""
import sqlite3

import pytest

from matching import (MIN_SCORE, score_pair, extract_words, text_part,
                      find_matches_for)


@pytest.fixture()
def neighbors():
    return {(1, 3), (3, 1), (2, 3), (3, 2)}  # Кафе-ГК, ГК-Библиотека


def make_item(type_, category_id, place_id, date, title, description="", photo=None):
    return {"id": 1, "user_id": 1, "category_id": category_id, "place_id": place_id,
            "type": type_, "title": title, "description": description,
            "date": date, "photo": photo, "status": "active"}


def test_full_match(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники",
                     "чёрные наушники с чехлом")
    found = make_item("found", 1, 1, "2026-11-02", "Нашёл наушники",
                      "нашёл наушники чёрные")
    result = score_pair(lost, found, neighbors)
    assert result is not None
    score, reasons = result
    assert 60 <= score <= 100
    assert score >= MIN_SCORE
    assert any("категория" in r for r in reasons)
    assert any("то же место" in r for r in reasons)


def test_other_category_rejected(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники", "чёрные")
    found = make_item("found", 2, 1, "2026-11-02", "Нашёл телефон", "чёрные")
    assert score_pair(lost, found, neighbors) is None


def test_found_before_lost_rejected(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-05", "Потерял наушники", "чёрные")
    found = make_item("found", 1, 1, "2026-11-01", "Нашёл наушники", "чёрные")
    assert score_pair(lost, found, neighbors) is None


def test_bad_dates_rejected(neighbors):
    lost = make_item("lost", 1, 1, "мусор", "Потерял наушники", "чёрные")
    found = make_item("found", 1, 1, "2026-11-01", "Нашёл наушники", "чёрные")
    assert score_pair(lost, found, neighbors) is None


def test_same_place_scores_more_than_neighbor(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники", "чёрные")
    same = make_item("found", 1, 1, "2026-11-02", "Нашёл наушники", "чёрные")
    neighbor = make_item("found", 1, 3, "2026-11-02", "Нашёл наушники", "чёрные")
    far = make_item("found", 1, 2, "2026-11-02", "Нашёл наушники", "чёрные")
    score_same = score_pair(lost, same, neighbors)[0]
    score_neighbor = score_pair(lost, neighbor, neighbors)[0]
    score_far = score_pair(lost, far, neighbors)[0]
    assert score_same > score_neighbor > score_far


def test_neighbor_place_reason(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники", "чёрные")
    neighbor = make_item("found", 1, 3, "2026-11-02", "Нашёл наушники", "чёрные")
    _, reasons = score_pair(lost, neighbor, neighbors)
    assert "соседнее место" in reasons


def test_text_stemming_tolerance(neighbors):
    # разные окончания одного слова должны совпадать
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники",
                     "чёрные наушники")
    found = make_item("found", 1, 1, "2026-11-02", "Нашёл наушник",
                      "наушник чёрный")
    score, reasons = score_pair(lost, found, neighbors)
    text_reasons = [r for r in reasons if r.startswith("общие слова")]
    assert text_reasons
    # все слова совпали — максимальный текстовый балл
    from matching import W_TEXT
    assert score >= 30 + 25 + 20 + W_TEXT


def test_photo_bonus(neighbors):
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники", "чёрные")
    found = make_item("found", 1, 1, "2026-11-02", "Нашёл наушники", "чёрные")
    lost_photo = make_item("lost", 1, 1, "2026-11-01", "Потерял наушники",
                           "чёрные", photo="a.png")
    found_photo = make_item("found", 1, 1, "2026-11-02", "Нашёл наушники",
                            "чёрные", photo="b.png")
    base = score_pair(lost, found, neighbors)[0]
    with_photo = score_pair(lost_photo, found_photo, neighbors)[0]
    assert with_photo == base + 10
    assert "есть фото у обоих" in score_pair(lost_photo, found_photo, neighbors)[1]


def test_threshold_boundary(neighbors):
    # пара ровно на границе порога: категория (30) + соседнее место (10)
    # + разница 14 дней (5) + текст с 1 общим словом
    lost = make_item("lost", 1, 1, "2026-11-01", "Потерял телефон",
                     "чёрный с чехлом и зарядкой")
    found = make_item("found", 1, 3, "2026-11-15", "Нашёл телефон",
                      "телефон на подоконнике")
    score, _ = score_pair(lost, found, neighbors)
    assert score is not None
    # проверяем, что порог осмыслен: слабые пары не проходят
    assert score < 60


def test_words_extraction():
    words = extract_words("Потерял чёрные наушники, в чехле! 12")
    assert "наушн" in words
    assert "чёрны" in words
    assert "12" not in words      # короче 3 символов
    assert "потер" not in words   # стоп-слово
    assert "чехле" in words


def test_text_part_empty():
    item = make_item("lost", 1, 1, "2026-11-01", "", "")
    assert text_part(item, item) == (0, [])


# --------------------- find_matches_for (работа с базой) ---------------------

@pytest.fixture()
def conn():
    import os
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


def insert_user(conn, email, name="Тест"):
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, contact) VALUES (?, ?, 'x', 'c')",
        (name, email))
    return cur.lastrowid


def insert_item(conn, user_id, type_, category_id=1, place_id=1,
                date="2026-11-01", title="Наушники", description="чёрные",
                status="active"):
    cur = conn.execute(
        "INSERT INTO items (user_id, category_id, place_id, type, title, "
        "description, date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, category_id, place_id, type_, title, description, date, status))
    return cur.lastrowid


def test_find_matches_creates_pair(conn):
    anna = insert_user(conn, "anna_m@example.com")
    dima = insert_user(conn, "dima_m@example.com")
    lost = insert_item(conn, anna, "lost", date="2026-11-01",
                       title="Потерял наушники", description="чёрные наушники")
    found = insert_item(conn, dima, "found", date="2026-11-02",
                        title="Нашёл наушники", description="нашёл наушники чёрные")
    conn.commit()
    added = find_matches_for(conn, found)
    conn.commit()
    assert added == 1
    row = conn.execute(
        "SELECT * FROM matches WHERE lost_item_id=? AND found_item_id=?",
        (lost, found)).fetchone()
    assert row is not None
    assert row["score"] >= MIN_SCORE
    assert row["status"] == "new"


def test_find_matches_no_duplicates(conn):
    anna = insert_user(conn, "anna_d@example.com")
    dima = insert_user(conn, "dima_d@example.com")
    insert_item(conn, anna, "lost", date="2026-11-01",
                title="Потерял наушники", description="чёрные наушники")
    found = insert_item(conn, dima, "found", date="2026-11-02",
                        title="Нашёл наушники", description="нашёл наушники чёрные")
    conn.commit()
    find_matches_for(conn, found)
    conn.commit()
    added_again = find_matches_for(conn, found)
    conn.commit()
    assert added_again == 0
    count = conn.execute("SELECT COUNT(*) AS n FROM matches").fetchone()["n"]
    assert count == 1


def test_find_matches_same_author_skipped(conn):
    user = insert_user(conn, "same_m@example.com")
    insert_item(conn, user, "lost", date="2026-11-01",
                title="Потерял наушники", description="чёрные наушники")
    found = insert_item(conn, user, "found", date="2026-11-02",
                        title="Нашёл наушники", description="нашёл наушники чёрные")
    conn.commit()
    added = find_matches_for(conn, found)
    assert added == 0


def test_find_matches_closed_candidate_skipped(conn):
    anna = insert_user(conn, "anna_c@example.com")
    dima = insert_user(conn, "dima_c@example.com")
    insert_item(conn, anna, "lost", date="2026-11-01",
                title="Потерял наушники", description="чёрные наушники",
                status="closed")
    found = insert_item(conn, dima, "found", date="2026-11-02",
                        title="Нашёл наушники", description="нашёл наушники чёрные")
    conn.commit()
    added = find_matches_for(conn, found)
    assert added == 0
