# -*- coding: utf-8 -*-
"""Тесты валидации объявления, фото, поиска, фильтров и пагинации."""
import io
import struct
import zlib

from conftest import add_item


def png_bytes(w=300, h=200):
    """Минимальный корректный PNG."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x30\x60\x90" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def base_form(**overrides):
    data = {"type": "lost", "title": "Чёрные наушники", "description": "описание",
            "category_id": "1", "place_id": "1", "date": "2026-11-01"}
    data.update(overrides)
    return data


def count_items():
    import os
    import sqlite3
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    n = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.close()
    return n


# ------------------------------- Валидация -------------------------------

def test_add_requires_login(client):
    r = client.post("/add", data=base_form(), follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_add_empty_form(client, user):
    before = count_items()
    r = client.post("/add", data={"type": "", "title": "", "description": "",
                                  "category_id": "", "place_id": "", "date": ""})
    assert r.status_code == 200
    html = r.data.decode("utf-8")
    assert "Выберите тип объявления" in html
    assert "Введите название (от 3 до 100 символов)" in html
    assert "Выберите категорию из списка" in html
    assert "Выберите место из списка" in html
    assert "Введите корректную дату" in html
    assert count_items() == before


def test_add_wrong_type(client, user):
    r = client.post("/add", data=base_form(type="sale"))
    assert r.status_code == 200
    assert "Выберите тип объявления" in r.data.decode("utf-8")


def test_add_nonexistent_category(client, user):
    r = client.post("/add", data=base_form(category_id="9999"))
    assert r.status_code == 200
    assert "Выберите категорию из списка" in r.data.decode("utf-8")


def test_add_nonnumeric_place(client, user):
    r = client.post("/add", data=base_form(place_id="abc"))
    assert r.status_code == 200
    assert "Выберите место из списка" in r.data.decode("utf-8")


def test_add_future_date(client, user):
    r = client.post("/add", data=base_form(date="2999-01-01"))
    assert r.status_code == 200
    assert "Дата не может быть в будущем" in r.data.decode("utf-8")


def test_add_bad_date(client, user):
    r = client.post("/add", data=base_form(date="abc"))
    assert r.status_code == 200
    assert "Введите корректную дату" in r.data.decode("utf-8")


def test_add_title_too_short(client, user):
    r = client.post("/add", data=base_form(title="аб"))
    assert r.status_code == 200
    assert "Введите название (от 3 до 100 символов)" in r.data.decode("utf-8")


def test_add_title_too_long(client, user):
    r = client.post("/add", data=base_form(title="а" * 101))
    assert r.status_code == 200
    assert "Введите название (от 3 до 100 символов)" in r.data.decode("utf-8")


def test_add_description_too_long(client, user):
    r = client.post("/add", data=base_form(description="ж" * 1001))
    assert r.status_code == 200
    assert "Описание не должно быть длиннее 1000 символов" in r.data.decode("utf-8")


def test_add_no_record_on_error(client, user):
    before = count_items()
    for overrides in ({"type": "x"}, {"category_id": "9999"}, {"place_id": "abc"},
                      {"date": "2999-01-01"}, {"title": "аб"}, {"title": "а" * 101},
                      {"description": "ж" * 1001}):
        client.post("/add", data=base_form(**overrides))
    assert count_items() == before


def test_add_get_prefills_type(client, user):
    r = client.get("/add?type=found")
    html = r.data.decode("utf-8")
    assert 'value="found"' in html


def test_add_form_keeps_values_on_error(client, user):
    r = client.post("/add", data=base_form(title="аб", place_id="abc"))
    html = r.data.decode("utf-8")
    assert 'value="аб"' in html          # введённый заголовок сохранён


def test_add_success_without_photo(client, user):
    item_id = add_item(client)
    assert item_id is not None
    r = client.get(f"/item/{item_id}")
    assert r.status_code == 200


# ---------------------------------- Фото ----------------------------------

def test_add_with_png_photo(client, user, tmp_path):
    r = client.post("/add", data={**base_form(title="Рюкзак Nike"),
                                  "photo": (io.BytesIO(png_bytes()), "photo.png")},
                    content_type="multipart/form-data", follow_redirects=False)
    assert r.status_code == 302
    assert "/item/" in r.headers["Location"]
    item_id = r.headers["Location"].split("/item/")[1]
    r = client.get(f"/item/{item_id}")
    html = r.data.decode("utf-8")
    assert "/uploads/" in html
    # файл сохранён под uuid-именем, исходное имя не используется
    upload_dir = __import__("os").environ["UPLOAD_DIR"]
    files = __import__("os").listdir(upload_dir)
    assert len(files) == 1
    assert "photo" not in files[0]


def test_add_fake_jpg_rejected(client, user):
    before = count_items()
    r = client.post("/add", data={**base_form(),
                                  "photo": (io.BytesIO(b"plain text"), "fake.jpg")},
                    content_type="multipart/form-data")
    html = r.data.decode("utf-8")
    assert count_items() == before
    assert "Допустимы только изображения" in html


def test_add_oversized_file_rejected(client, user):
    r = client.post("/add", data={**base_form(),
                                  "photo": (io.BytesIO(b"\x00" * (6 * 1024 * 1024)), "big.png")},
                    content_type="multipart/form-data", follow_redirects=True)
    html = r.data.decode("utf-8")
    assert "Файл слишком большой, максимум 5 МБ" in html


def test_uploads_traversal_blocked(client, user):
    r = client.get("/uploads/../app.py")
    assert r.status_code == 404


# ------------------------- Поиск, фильтры, пагинация -------------------------

def test_search_cyrillic_case_insensitive(client, user):
    add_item(client, title="беспроводные наушники")
    r = client.get("/items?type=lost&q=" + "Наушники")
    html = r.data.decode("utf-8")
    assert "беспроводные наушники" in html


def test_search_escapes_like_specials(client, user):
    add_item(client, title="Простая вещь")
    r = client.get("/items?type=lost&q=" + "вещь%_")
    assert r.status_code == 200
    assert "Простая вещь" not in r.data.decode("utf-8")


def test_filter_category(client, user):
    add_item(client, title="Зонт голубой", category_id="6")
    add_item(client, title="Перчатка красная", category_id="1")
    r = client.get("/items?type=lost&category_id=6")
    html = r.data.decode("utf-8")
    assert "Зонт голубой" in html
    assert "Перчатка красная" not in html


def test_filter_place(client, user):
    add_item(client, title="Вещь в Кафе", place_id="1")
    add_item(client, title="Вещь в Спортзале", place_id="5")
    r = client.get("/items?type=lost&place_id=5")
    html = r.data.decode("utf-8")
    assert "Вещь в Спортзале" in html
    assert "Вещь в Кафе" not in html


def test_filter_date(client, user):
    add_item(client, title="Новое", date="2026-11-05")
    add_item(client, title="Старое", date="2026-10-01")
    r = client.get("/items?type=lost&date=2026-11-01")
    html = r.data.decode("utf-8")
    assert "Новое" in html
    assert "Старое" not in html


def test_invalid_params_ignored(client, user):
    for qs in ["?type=abc", "?category_id=abc", "?category_id=9999",
               "?place_id=9999", "?date=abc", "?page=abc"]:
        r = client.get("/items" + qs)
        assert r.status_code == 200


def test_empty_states(client, user):
    r = client.get("/items?type=lost")
    html = r.data.decode("utf-8")
    assert "Пока нет объявлений" in html
    assert "Создать первое объявление" in html
    r = client.get("/items?type=lost&q=" + "несуществующийтекст")
    html = r.data.decode("utf-8")
    assert "По вашему запросу ничего не найдено" in html
    assert "Сбросить фильтры" in html


def test_pagination(client, user):
    for i in range(20):
        add_item(client, title=f"Тестовое объявление {i}")
    r = client.get("/items?type=lost")
    html = r.data.decode("utf-8")
    assert "Найдено объявлений: 20" in html
    assert "Вперёд" in html
    r = client.get("/items?type=lost&page=2")
    html = r.data.decode("utf-8")
    assert "Назад" in html and "Вперёд" in html
    r = client.get("/items?type=lost&page=999")
    html = r.data.decode("utf-8")
    assert "Назад" in html and "Вперёд" not in html
    r = client.get("/items?type=lost&page=abc")
    assert r.status_code == 200


def test_pagination_keeps_filters(client, user):
    for i in range(10):
        add_item(client, title=f"Наушники {i}", category_id="1")
    r = client.get("/items?type=lost&category_id=1")
    html = r.data.decode("utf-8")
    assert "category_id=1" in html and "page=2" in html


def test_home_pagination(client, user):
    for i in range(10):
        add_item(client, title=f"Объявление {i}")
    r = client.get("/")
    html = r.data.decode("utf-8")
    assert "page=2" in html
    r = client.get("/?page=999")
    assert r.status_code == 200
