# -*- coding: utf-8 -*-
"""Тесты авторизации, прав доступа, совпадений и закрытия объявлений."""
import os
import sqlite3

from conftest import register_and_login, add_item

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def db():
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.row_factory = sqlite3.Row
    return conn


def user_id_of(email):
    conn = db()
    uid = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
    conn.close()
    return uid


def set_password(email, password_hash):
    conn = db()
    conn.execute("UPDATE users SET password_hash = ? WHERE email = ?",
                 (password_hash, email))
    conn.commit()
    conn.close()


# --------------------------- Доступ гостей ---------------------------

def test_guest_redirect_from_add(client):
    r = client.get("/add", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_guest_redirect_from_dashboard(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_guest_redirect_from_match_actions(client):
    r = client.post("/match/1/confirm", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


# --------------------------- Регистрация ---------------------------

def test_register_success(client):
    r = client.post("/register", data={
        "name": "Аня Тестова", "email": "reg1@example.com",
        "password": "password123", "password2": "password123"},
        follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_register_duplicate_email(client):
    for _ in range(2):
        r = client.post("/register", data={
            "name": "Аня Тестова", "email": "dup@example.com",
            "password": "password123", "password2": "password123"},
            follow_redirects=True)
    assert "Этот адрес электронной почты уже зарегистрирован" in r.data.decode("utf-8")


def test_register_short_password(client):
    r = client.post("/register", data={
        "name": "Аня Тестова", "email": "short@example.com",
        "password": "1234567", "password2": "1234567"}, follow_redirects=True)
    assert "Пароль должен содержать не менее 8 символов" in r.data.decode("utf-8")


def test_register_password_mismatch(client):
    r = client.post("/register", data={
        "name": "Аня Тестова", "email": "mismatch@example.com",
        "password": "password123", "password2": "password999"},
        follow_redirects=True)
    assert "Пароли не совпадают" in r.data.decode("utf-8")


def test_register_bad_name(client):
    r = client.post("/register", data={
        "name": "Аня", "email": "name@example.com",
        "password": "password123", "password2": "password123"},
        follow_redirects=True)
    assert "Введите имя и фамилию" in r.data.decode("utf-8")


def test_register_bad_email(client):
    r = client.post("/register", data={
        "name": "Аня Тестова", "email": "not-an-email",
        "password": "password123", "password2": "password123"},
        follow_redirects=True)
    assert "Введите корректный адрес электронной почты" in r.data.decode("utf-8")


# ------------------------------- Вход --------------------------------

def test_login_wrong_password(client):
    register_and_login(client, "login1@example.com")
    from werkzeug.security import generate_password_hash
    set_password("login1@example.com", generate_password_hash("correct-password"))
    client.post("/logout")
    r = client.post("/login", data={"email": "login1@example.com",
                                    "password": "wrong-password"},
                    follow_redirects=True)
    assert "Неверная почта или пароль" in r.data.decode("utf-8")


def test_login_unknown_email(client):
    r = client.post("/login", data={"email": "ghost@example.com",
                                    "password": "whatever123"},
                    follow_redirects=True)
    assert "Неверная почта или пароль" in r.data.decode("utf-8")


# ------------------------------ Права --------------------------------

def test_contact_hidden_from_guest(client, user):
    add_item(client)
    client.post("/logout")
    r = client.get("/item/1")
    html = r.data.decode("utf-8")
    assert "Войдите" in html


def test_contact_visible_to_logged_in(client, user):
    item_id = add_item(client)
    client.post("/logout")
    register_and_login(client, "other@example.com", name="Другой Юзер")
    r = client.get(f"/item/{item_id}")
    html = r.data.decode("utf-8")
    assert "+7 900 000-00-00" in html


def test_close_other_users_item_forbidden(client, user):
    item_id = add_item(client)
    client.post("/logout")
    register_and_login(client, "stranger@example.com", name="Чужой Юзер")
    r = client.post(f"/item/{item_id}/close", follow_redirects=False)
    assert r.status_code == 403


def test_close_own_item(client, user):
    item_id = add_item(client)
    r = client.post(f"/item/{item_id}/close", follow_redirects=False)
    assert r.status_code == 302
    conn = db()
    status = conn.execute("SELECT status FROM items WHERE id=?",
                          (item_id,)).fetchone()[0]
    conn.close()
    assert status == "closed"


def test_closed_item_disappears_from_home_and_matches(client, user):
    item_id = add_item(client, title="Исчезающая вещь")
    # совпадение с самим собой не создаётся, поэтому проверяем ленту
    client.post(f"/item/{item_id}/close")
    r = client.get("/")
    html = r.data.decode("utf-8")
    assert "Исчезающая вещь" not in html
    r = client.get("/items?type=lost")
    assert "Исчезающая вещь" not in r.data.decode("utf-8")


# ---------------------------- Совпадения -----------------------------

def _make_match_pair(client, lost_email, found_email):
    """Публикует пару «потерял/нашёл» двумя пользователями.
    Возвращает словарь с id match, потерянного и найденного объявлений."""
    register_and_login(client, lost_email, name="Потерявший Юзер")
    lost_id = add_item(client, title="Потерял наушники",
                       description="чёрные наушники с чехлом")
    client.post("/logout")
    register_and_login(client, found_email, name="Нашедший Юзер")
    found_id = add_item(client, title="Нашёл наушники", type="found",
                        description="нашёл наушники чёрные")
    client.post("/logout")
    conn = db()
    row = conn.execute(
        "SELECT * FROM matches WHERE found_item_id = ?", (found_id,)).fetchone()
    conn.close()
    return {"match": row, "lost_id": lost_id, "found_id": found_id}


def test_match_shown_with_buttons_to_lost_author(client):
    pair = _make_match_pair(client, "m_lost@example.com", "m_found@example.com")
    assert pair["match"] is not None
    client.post("/login", data={"email": "m_lost@example.com", "password": "password123"})
    r = client.get(f"/item/{pair['lost_id']}")
    html = r.data.decode("utf-8")
    assert "Возможно, эта вещь соответствует" in html
    assert "Это моё" in html
    assert "Не подходит" in html
    assert "Оценка системы" in html


def test_match_without_buttons_for_found_author(client):
    pair = _make_match_pair(client, "m2_lost@example.com", "m2_found@example.com")
    client.post("/login", data={"email": "m2_found@example.com", "password": "password123"})
    r = client.get(f"/item/{pair['found_id']}")
    html = r.data.decode("utf-8")
    assert "Возможно, эта вещь соответствует" in html
    assert "Это моё" not in html


def test_confirm_by_lost_author(client):
    pair = _make_match_pair(client, "m3_lost@example.com", "m3_found@example.com")
    client.post("/login", data={"email": "m3_lost@example.com", "password": "password123"})
    r = client.post(f"/match/{pair['match']['id']}/confirm", data={"next": "/dashboard"},
                    follow_redirects=True)
    assert "Контакты участников" in r.data.decode("utf-8")
    conn = db()
    status = conn.execute("SELECT status FROM matches WHERE id=?",
                          (pair["match"]["id"],)).fetchone()[0]
    conn.close()
    assert status == "confirmed"


def test_confirm_by_stranger_forbidden(client):
    pair = _make_match_pair(client, "m4_lost@example.com", "m4_found@example.com")
    register_and_login(client, "m4_stranger@example.com", name="Посторонний Юзер")
    r = client.post(f"/match/{pair['match']['id']}/confirm", follow_redirects=False)
    assert r.status_code == 403


def test_reject_by_stranger_forbidden(client):
    pair = _make_match_pair(client, "m5_lost@example.com", "m5_found@example.com")
    register_and_login(client, "m5_stranger@example.com", name="Посторонний Юзер")
    r = client.post(f"/match/{pair['match']['id']}/reject", follow_redirects=False)
    assert r.status_code == 403


def test_repeat_confirm_is_safe(client):
    pair = _make_match_pair(client, "m6_lost@example.com", "m6_found@example.com")
    client.post("/login", data={"email": "m6_lost@example.com", "password": "password123"})
    client.post(f"/match/{pair['match']['id']}/confirm", data={"next": "/dashboard"},
                follow_redirects=True)
    r = client.post(f"/match/{pair['match']['id']}/confirm", data={"next": "/dashboard"},
                    follow_redirects=True)
    assert "Это совпадение уже обработано" in r.data.decode("utf-8")
    conn = db()
    status = conn.execute("SELECT status FROM matches WHERE id=?",
                          (pair["match"]["id"],)).fetchone()[0]
    conn.close()
    assert status == "confirmed"


def test_reject_hides_match(client):
    pair = _make_match_pair(client, "m7_lost@example.com", "m7_found@example.com")
    client.post("/login", data={"email": "m7_lost@example.com", "password": "password123"})
    r = client.post(f"/match/{pair['match']['id']}/reject", data={"next": "/dashboard"},
                    follow_redirects=True)
    assert "Совпадение скрыто" in r.data.decode("utf-8")
    r = client.get(f"/item/{pair['lost_id']}")
    html = r.data.decode("utf-8")
    # отклонённое совпадение больше не показывается: нет ни карточки
    # найденной вещи, ни кнопок «Это моё»/«Не подходит»
    assert "Нашёл наушники" not in html
    assert "Это моё" not in html
    assert "Пока нет подходящих совпадений" in html


def test_match_not_found_404(client, user):
    r = client.post("/match/9999/confirm", follow_redirects=False)
    assert r.status_code == 404


def test_match_redirect_only_internal(client):
    pair = _make_match_pair(client, "m8_lost@example.com", "m8_found@example.com")
    client.post("/login", data={"email": "m8_lost@example.com", "password": "password123"})
    r = client.post(f"/match/{pair['match']['id']}/confirm",
                    data={"next": "https://evil.example.com"}, follow_redirects=False)
    # внешние адреса не допускаются: перебрасывает на внутреннюю страницу
    assert not r.headers["Location"].startswith("https://evil")


def test_confirm_requires_active_items(client):
    pair = _make_match_pair(client, "m9_lost@example.com", "m9_found@example.com")
    # закрываем найденное объявление
    client.post("/login", data={"email": "m9_found@example.com", "password": "password123"})
    client.post(f"/item/{pair['found_id']}/close")
    client.post("/logout")
    client.post("/login", data={"email": "m9_lost@example.com", "password": "password123"})
    r = client.post(f"/match/{pair['match']['id']}/confirm", data={"next": "/dashboard"},
                    follow_redirects=True)
    assert "Это совпадение уже обработано" in r.data.decode("utf-8")
    conn = db()
    status = conn.execute("SELECT status FROM matches WHERE id=?",
                          (pair["match"]["id"],)).fetchone()[0]
    conn.close()
    assert status == "new"


def test_dashboard_shows_suggested_matches(client):
    _make_match_pair(client, "m10_lost@example.com", "m10_found@example.com")
    client.post("/login", data={"email": "m10_lost@example.com", "password": "password123"})
    r = client.get("/dashboard")
    html = r.data.decode("utf-8")
    assert "Предложенные совпадения" in html
    assert "Это моё" in html


def test_dashboard_empty_matches(client, user):
    r = client.get("/dashboard")
    assert "Пока нет предложенных совпадений" in r.data.decode("utf-8")
