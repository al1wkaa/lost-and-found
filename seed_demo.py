# -*- coding: utf-8 -*-
"""Тестовые данные для сервиса «Нашлось!».

Создаёт 3 демо-пользователей (пароль demo12345) и 28 объявлений за
последние 30 дней относительно сегодняшней даты:
  - 7 пар «потерял и нашёл», которые должны совпасть (EXPECTED_MATCHES);
  - 6 «почти совпадений», которые не должны проходить порог
    (EXPECTED_NON_MATCHES);
  - одиночные объявления для ленты.

Скрипт идемпотентен: если демо-пользователи уже есть, данные не
дублируются. Ключ --reset удаляет только демо-данные (объявления,
совпадения и самих демо-пользователей) и создаёт их заново.

Запуск:  python seed_demo.py [--reset]
"""
import sys
from datetime import date, timedelta

from db import get_db, init_db
from matching import find_matches_for, MIN_SCORE
from werkzeug.security import generate_password_hash

DEMO_EMAILS = ["demo1@example.com", "demo2@example.com", "demo3@example.com"]
DEMO_USERS = [
    # email, имя, контакт
    ("demo1@example.com", "Анна Демидова", "+7 900 111-11-11"),
    ("demo2@example.com", "Дмитрий Петров", "+7 900 222-22-22"),
    ("demo3@example.com", "Мария Соколова", "@maria_demo"),
]
DEMO_PASSWORD = "demo12345"

# ---------------------- Ожидания для оценки алгоритма ----------------------
# (заголовок потерянного, заголовок найденного) — должны совпасть
EXPECTED_MATCHES = [
    ("Потерял беспроводные наушники", "Нашёл наушники"),
    ("Потерял телефон Samsung", "Нашёл телефон Samsung"),
    ("Потерял связку ключей от квартиры", "Нашёл связку ключей"),
    ("Потерял студенческий билет", "Нашёл студенческий билет"),
    ("Потерял спортивную куртку", "Нашёл куртку"),
    ("Потерял наушники JBL", "Нашёл наушники JBL"),
    ("Потерял телефон в спортзале", "Нашёл телефон"),
]

# «Почти совпадения» — НЕ должны проходить порог:
#  1-2: другая категория / находка раньше потери (отбрасываются правилами)
#  3-4: далёкое место, разница дат больше 14 дней
#  5-6: общие слова есть, но место и время не подходят
EXPECTED_NON_MATCHES = [
    ("Потерял чёрные наушники Sony", "Нашёл ключи с брелоком"),
    ("Потерял телефон Xiaomi", "Нашёл телефон Xiaomi красный"),
    ("Потерял рюкзак Nike", "Нашёл рюкзак с ноутбуком"),
    ("Потерял зачётку", "Нашёл зачётку"),
    ("Потерял наушники AirPods", "Нашёл наушники AirPods"),
    ("Потерял наушники Earbuds", "Нашёл наушники Earbuds в автобусе"),
]

# ------------------------------ Объявления ------------------------------
# (email автора, тип, категория, место, сколько дней назад, заголовок, описание)
# Категории: Наушники, Телефон, Ключи, Документы, Одежда, Другое
# Места: Кафе, Библиотека, Главный корпус, Общежитие, Спортзал, Остановка
ITEMS = [
    # --- ожидаемые пары (7) ---
    ("demo1@example.com", "lost", "Наушники", "Кафе", 26,
     "Потерял беспроводные наушники", "чёрные наушники в синем чехле"),
    ("demo2@example.com", "found", "Наушники", "Кафе", 24,
     "Нашёл наушники", "нашёл беспроводные наушники в чехле"),

    ("demo2@example.com", "lost", "Телефон", "Библиотека", 20,
     "Потерял телефон Samsung", "чёрный смартфон Samsung Galaxy"),
    ("demo1@example.com", "found", "Телефон", "Библиотека", 19,
     "Нашёл телефон Samsung", "нашёл смартфон Samsung, включён"),

    ("demo1@example.com", "lost", "Ключи", "Главный корпус", 17,
     "Потерял связку ключей от квартиры", "брелок в виде кота"),
    ("demo3@example.com", "found", "Ключи", "Кафе", 17,
     "Нашёл связку ключей", "на брелке кот"),

    ("demo3@example.com", "lost", "Документы", "Общежитие", 14,
     "Потерял студенческий билет", "студенческий билет с фото"),
    ("demo1@example.com", "found", "Документы", "Общежитие", 11,
     "Нашёл студенческий билет", "нашёл студенческий билет на столе"),

    ("demo2@example.com", "lost", "Одежда", "Общежитие", 9,
     "Потерял спортивную куртку", "синяя куртка Nike"),
    ("demo3@example.com", "found", "Одежда", "Спортзал", 7,
     "Нашёл куртку", "куртка Nike в спортзале"),

    ("demo3@example.com", "lost", "Наушники", "Остановка", 5,
     "Потерял наушники JBL", "белые накладные наушники"),
    ("demo2@example.com", "found", "Наушники", "Остановка", 1,
     "Нашёл наушники JBL", "наушники белые, накладные"),

    ("demo1@example.com", "lost", "Телефон", "Спортзал", 4,
     "Потерял телефон в спортзале", "чехол с наклейкой"),
    ("demo2@example.com", "found", "Телефон", "Спортзал", 2,
     "Нашёл телефон", "телефон в чехле с наклейкой"),

    # --- «почти совпадения» (6), порог не проходят ---
    # 1: другая категория
    ("demo1@example.com", "lost", "Наушники", "Библиотека", 15,
     "Потерял чёрные наушники Sony", "полноразмерные, провод"),
    ("demo2@example.com", "found", "Ключи", "Библиотека", 13,
     "Нашёл ключи с брелоком", "брелок мягкая игрушка"),
    # 2: находка раньше потери
    ("demo1@example.com", "lost", "Телефон", "Главный корпус", 12,
     "Потерял телефон Xiaomi", "красный чехол, стилус"),
    ("demo2@example.com", "found", "Телефон", "Главный корпус", 15,
     "Нашёл телефон Xiaomi красный", "на парту в аудитории"),
    # 3: далёкое место
    ("demo3@example.com", "lost", "Другое", "Кафе", 8,
     "Потерял рюкзак Nike", "чёрный, цвета графит"),
    ("demo1@example.com", "found", "Другое", "Остановка", 8,
     "Нашёл рюкзак с ноутбуком", "серый рюкзак"),
    # 4: разница дат больше 14 дней
    ("demo2@example.com", "lost", "Документы", "Главный корпус", 25,
     "Потерял зачётку", "зачётная книжка, 2 курс"),
    ("demo3@example.com", "found", "Документы", "Библиотека", 1,
     "Нашёл зачётку", "на столе в читальном зале"),
    # 5-6: общие слова есть, но место и время не подходят
    ("demo1@example.com", "lost", "Наушники", "Кафе", 21,
     "Потерял наушники AirPods", "белые, кейс поцарапан"),
    ("demo2@example.com", "found", "Наушники", "Спортзал", 2,
     "Нашёл наушники AirPods", "у шкафа в раздевалке"),
    ("demo3@example.com", "lost", "Наушники", "Библиотека", 11,
     "Потерял наушники Earbuds", "вкладыши, серые"),
    ("demo1@example.com", "found", "Наушники", "Общежитие", 0,
     "Нашёл наушники Earbuds в автобусе", "передал в общежитие дежурному"),

    # --- одиночные объявления для ленты ---
    ("demo3@example.com", "found", "Другое", "Остановка", 16,
     "Нашёл розовый зонт", "зонт лежал на скамейке"),
    ("demo2@example.com", "lost", "Другое", "Спортзал", 22,
     "Потерял зарядку для ноутбука", "блок питания Apple"),
]


def demo_user_ids(conn):
    rows = conn.execute(
        "SELECT id, email FROM users WHERE email IN (?, ?, ?)", DEMO_EMAILS
    ).fetchall()
    return {row["email"]: row["id"] for row in rows}


def delete_demo_data(conn):
    """Удаляет только демо-данные: их объявления, совпадения и самих пользователей."""
    ids = list(demo_user_ids(conn).values())
    if not ids:
        return
    marks = ",".join("?" * len(ids))
    conn.execute(
        "DELETE FROM matches WHERE lost_item_id IN "
        "(SELECT id FROM items WHERE user_id IN (%s)) "
        "OR found_item_id IN (SELECT id FROM items WHERE user_id IN (%s))" % (marks, marks),
        ids + ids)
    conn.execute("DELETE FROM items WHERE user_id IN (%s)" % marks, ids)
    conn.execute("DELETE FROM users WHERE id IN (%s)" % marks, ids)


def create_users(conn):
    for email, name, contact in DEMO_USERS:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, contact) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(DEMO_PASSWORD), contact))


def create_items(conn):
    today = date.today()
    titles = {}
    for email, item_type, category, place, days_ago, title, description in ITEMS:
        item_date = (today - timedelta(days=days_ago)).isoformat()
        cur = conn.execute(
            "INSERT INTO items (user_id, category_id, place_id, type, title, "
            "description, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_ids[email], category_ids[category], place_ids[place],
             item_type, title, description, item_date))
        titles[title] = cur.lastrowid
    return titles


def verify(titles):
    """Проверяет, что ожидаемые пары совпали, а «почти совпадения» — нет."""
    conn = get_db()
    ok = True
    print("\nОжидаемые пары (должны быть в matches):")
    for lost_title, found_title in EXPECTED_MATCHES:
        row = conn.execute(
            "SELECT m.score, m.status FROM matches m "
            "WHERE m.lost_item_id = ? AND m.found_item_id = ?",
            (titles[lost_title], titles[found_title])).fetchone()
        status = "ок" if row and row["score"] >= MIN_SCORE else "НЕ НАЙДЕНА"
        if row is None or row["score"] < MIN_SCORE:
            ok = False
        score = row["score"] if row else "-"
        print(f"  [{status}] {lost_title} -> {found_title}, балл {score}")

    print("\n«Почти совпадения» (не должны быть в matches):")
    for lost_title, found_title in EXPECTED_NON_MATCHES:
        row = conn.execute(
            "SELECT m.score FROM matches m "
            "WHERE m.lost_item_id = ? AND m.found_item_id = ?",
            (titles[lost_title], titles[found_title])).fetchone()
        if row is None:
            print(f"  [ок] {lost_title} -> {found_title}")
        else:
            ok = False
            print(f"  [ОШИБКА: пара с баллом {row['score']}] "
                  f"{lost_title} -> {found_title}")
    conn.close()
    return ok


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    init_db()
    conn = get_db()

    if demo_user_ids(conn) and not reset:
        print("Демо-данные уже существуют, ничего не добавлено "
              "(для пересоздания запустите: python seed_demo.py --reset)")
        conn.close()
        sys.exit(0)

    if reset:
        print("Удаляю демо-данные...")
        delete_demo_data(conn)

    create_users(conn)
    conn.commit()

    user_ids = {row["email"]: row["id"] for row in
                conn.execute("SELECT id, email FROM users WHERE email IN (?, ?, ?)",
                             DEMO_EMAILS).fetchall()}
    category_ids = {row["name"]: row["id"] for row in
                    conn.execute("SELECT id, name FROM categories").fetchall()}
    place_ids = {row["name"]: row["id"] for row in
                 conn.execute("SELECT id, name FROM places").fetchall()}

    titles = create_items(conn)
    conn.commit()

    # подбор совпадений для каждого нового объявления
    added = 0
    for item_id in titles.values():
        added += find_matches_for(conn, item_id)
    conn.commit()
    conn.close()

    print(f"Создано пользователей: {len(DEMO_USERS)}, объявлений: {len(ITEMS)}, "
          f"добавлено совпадений: {added}")
    ok = verify(titles)
    print("\nИтог:", "все ожидания выполнены" if ok else "ЕСТЬ РАСХОЖДЕНИЯ")
    print("Демо-аккаунты: demo1@example.com, demo2@example.com, "
          "demo3@example.com (пароль demo12345)")
    sys.exit(0 if ok else 1)
