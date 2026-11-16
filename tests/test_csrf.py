# -*- coding: utf-8 -*-
"""Тест CSRF-защиты: POST без токена отклоняется.

База и приложение настраиваются в conftest.py (CSRF включена —
это конфигурация по умолчанию, в отличие от fixture app).
"""
import re

import app as app_module  # noqa: F401  (импорт через conftest)
import pytest


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = True  # CSRF включена
    return app_module.app.test_client()


def test_post_without_token_rejected(client):
    r = client.post("/register", data={"name": "Аня Тест", "email": "csrf_x@example.com",
                                       "password": "password123",
                                       "password2": "password123"},
                    follow_redirects=False)
    assert r.status_code == 302
    r = client.get(r.headers["Location"])
    assert "Сессия устарела, повторите действие" in r.data.decode("utf-8")


def test_forms_contain_token(client):
    for page in ["/register", "/login", "/add"]:
        r = client.get(page, follow_redirects=True)
        assert 'name="csrf_token"' in r.data.decode("utf-8"), page


def test_post_with_token_works(client):
    r = client.get("/register")
    token = re.search(r'name="csrf_token" value="([^"]+)"',
                      r.data.decode("utf-8")).group(1)
    r = client.post("/register", data={"name": "Аня Тест", "email": "csrf_ok@example.com",
                                       "password": "password123",
                                       "password2": "password123",
                                       "csrf_token": token}, follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]
