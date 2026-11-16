# -*- coding: utf-8 -*-
"""Подбор весов алгоритма совпадений на тестовых данных seed_demo.py.

Загружает демо-данные во временную базу, считает оценки для ВСЕХ пар
«потерял и нашёл» (включая отброшенные правилами — они помечены «—»),
печатает таблицу: ожидаемые пары с баллами, самые высокие «ложные»
пары и итог по полноте (сколько ожидаемых пар прошли порог) и точности
(сколько посторонних пар прошли порог).

Запуск:
    python tune_matching.py            # свежая временная база + seed_demo
    python tune_matching.py --db путь  # оценить указанную базу
"""
import argparse
import os
import sys
import tempfile

parser = argparse.ArgumentParser(description="Подбор весов алгоритма совпадений")
parser.add_argument("--db", help="путь к готовой базе с демо-данными")
args = parser.parse_args()

if not args.db:
    db_path = os.path.join(tempfile.gettempdir(), "lf_tune_demo.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ["DATABASE_PATH"] = db_path
    os.environ.setdefault("UPLOAD_DIR", tempfile.gettempdir())

import matching  # noqa: E402  (импорт после задания DATABASE_PATH)
import seed_demo  # noqa: E402
from db import get_db  # noqa: E402

if not args.db:
    # создаём демо-данные во временной базе
    conn = get_db()
    from db import init_db
    init_db()
    seed_demo.delete_demo_data(conn)
    seed_demo.create_users(conn)
    conn.commit()
    seed_demo.user_ids = {row["email"]: row["id"] for row in
                          conn.execute("SELECT id, email FROM users WHERE email IN (?, ?, ?)",
                                       seed_demo.DEMO_EMAILS).fetchall()}
    seed_demo.category_ids = {row["name"]: row["id"] for row in
                              conn.execute("SELECT id, name FROM categories").fetchall()}
    seed_demo.place_ids = {row["name"]: row["id"] for row in
                           conn.execute("SELECT id, name FROM places").fetchall()}
    seed_demo.create_items(conn)
    conn.commit()
    conn.close()

expected_pairs = set(seed_demo.EXPECTED_MATCHES)
near_misses = set(seed_demo.EXPECTED_NON_MATCHES)


def title_of(item):
    return item["title"]


conn = get_db()
items = [dict(row) for row in conn.execute("SELECT * FROM items").fetchall()]
neighbors = matching.load_neighbor_pairs(conn)
conn.close()

lost_items = [i for i in items if i["type"] == "lost"]
found_items = [i for i in items if i["type"] == "found"]

rows = []  # (балл|None, пара, метка)
for lost in lost_items:
    for found in found_items:
        result = matching.score_pair(lost, found, neighbors)
        score = result[0] if result else None
        pair = (title_of(lost), title_of(found))
        if pair in expected_pairs:
            mark = "ОЖИДАЕМАЯ"
        elif pair in near_misses:
            mark = "почти"
        else:
            mark = "посторонняя"
        rows.append((score, pair, mark, lost["user_id"] == found["user_id"]))

min_score = matching.MIN_SCORE

print(f"Константы: W_CATEGORY={matching.W_CATEGORY}, W_PLACE={matching.W_PLACE}, "
      f"W_TIME={matching.W_TIME}, W_TEXT={matching.W_TEXT}, W_PHOTO={matching.W_PHOTO}, "
      f"PLACE_SAME={matching.PLACE_SAME}, PLACE_NEIGHBOR={matching.PLACE_NEIGHBOR}, "
      f"TIME_STEPS={matching.TIME_STEPS}, MIN_SCORE={min_score}")
print()

print("=== Ожидаемые пары (должны пройти порог) ===")
recall = 0
for score, pair, mark, same_author in rows:
    if mark != "ОЖИДАЕМАЯ":
        continue
    passed = score is not None and score >= min_score
    recall += passed
    shown = score if score is not None else "—"
    print(f"  [{'+прошла' if passed else 'НЕ прошла'}] балл {shown:>3}  {pair[0]}  <->  {pair[1]}")
print(f"Полнота: {recall} из {len(expected_pairs)}")

print()
print("=== Самые высокие посторонние и «почти» пары (не должны пройти) ===")
false_rows = sorted((r for r in rows if r[2] != "ОЖИДАЕМАЯ"),
                    key=lambda r: r[0] if r[0] is not None else -1, reverse=True)
false_passed = 0
total_false = 0
for score, pair, mark, same_author in false_rows[:15]:
    passed = score is not None and score >= min_score
    total_false += 1
    false_passed += passed
    author = " (один автор)" if same_author else ""
    print(f"  [{'ПРОШЛА!' if passed else 'ок'}] балл {score if score is not None else '—':>3}  "
          f"[{mark}{author}]  {pair[0]}  <->  {pair[1]}")

all_false = [r for r in rows if r[2] != "ОЖИДАЕМАЯ"]
false_passed_total = sum(1 for s, _, _, _ in all_false if s is not None and s >= min_score)
print()
print(f"Итог: полнота {recall}/{len(expected_pairs)}, "
      f"точность: посторонних пар прошло порог {false_passed_total} из {len(all_false)}")
if recall == len(expected_pairs) and false_passed_total == 0:
    print("Цель достигнута: все ожидаемые пары прошли порог, посторонние — нет.")
else:
    print("Цель НЕ достигнута — подберите константы в matching.py.")
