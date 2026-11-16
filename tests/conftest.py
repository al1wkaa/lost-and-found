# -*- coding: utf-8 -*-
"""Общие фикстуры pytest: приложение на временной базе, клиент, вход."""
import os
import sys
import tempfile

import pytest

# DATABASE_PATH и UPLOAD_DIR задаются ДО импорта приложения
TEST_DIR = tempfile.mkdtemp(prefix="lf_tests_")
os.environ["DATABASE_PATH"] = os.path.join(TEST_DIR, "test.db")
os.environ["UPLOAD_DIR"] = os.path.join(TEST_DIR, "uploads")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    """Чистит пользовательские данные после каждого теста.

    Справочники (категории, места, соседи) остаются, чтобы не пересоздавать
    их в каждом тесте: удаляются только совпадения, объявления и пользователи.
    """
    yield
    import sqlite3
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in ("matches", "items", "users"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


@pytest.fixture()
def app():
    app_module.app.config.update(
        WTF_CSRF_ENABLED=False,
        TESTING=True,
    )
    return app_module.app


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, email, name="Тест Пользователь",
                       password="password123", contact="+7 900 000-00-00"):
    """Регистрирует пользователя и входит в его аккаунт."""
    client.post("/register", data={
        "name": name, "email": email, "password": password,
        "password2": password, "contact": contact})
    client.post("/login", data={"email": email, "password": password})


@pytest.fixture()
def user(client):
    """Создаёт и возвращает email первого пользователя (уже вошёл)."""
    register_and_login(client, "user1@example.com")
    return "user1@example.com"


def add_item(client, **overrides):
    """Публикует объявление, возвращает url страницы (без /item/)."""
    data = {
        "type": "lost", "title": "Чёрные наушники", "description": "описание",
        "category_id": "1", "place_id": "1", "date": "2026-11-01",
    }
    data.update(overrides)
    r = client.post("/add", data=data, follow_redirects=False)
    location = r.headers.get("Location", "")
    if "/item/" in location:
        return int(location.split("/item/")[1])
    return None
