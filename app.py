import os
import sqlite3
import uuid
from datetime import date, datetime
from io import BytesIO

from flask import (Flask, render_template, request, redirect, url_for, flash,
                   abort, send_from_directory)
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db, init_db

app = Flask(__name__)
# Секретный ключ подписывает сессии. На хостинге задайте свой через переменную окружения SECRET_KEY.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
# Папка для фотографий объявлений (поле items.photo), путь можно переопределить через UPLOAD_DIR
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads")
# Максимум для загружаемых файлов (включая фото): 5 МБ
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
init_db()

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Войдите, чтобы открыть эту страницу."
login_manager.login_message_category = "warning"


@app.template_filter("ru_date")
def ru_date(value):
    """Дата из базы (YYYY-MM-DD) в формат вёрстки DD.MM.YYYY."""
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return value


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.name = row["name"]
        self.email = row["email"]
        self.contact = row["contact"]


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return User(row) if row else None


def is_safe_next(target):
    """Разрешаем перенаправление только на страницы нашего же сайта."""
    return bool(target) and target.startswith("/") and not target.startswith("//")


# ------------------------- Вспомогательные функции -------------------------

PER_PAGE = 9  # объявлений на одной странице ленты

# Реальные форматы изображений, которые принимает сервер (проверяется содержимое,
# а не имя файла или MIME-тип), и расширения для сохранения
ALLOWED_PHOTO_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
MAX_PHOTO_SIDE = 1600  # длинная сторона фото после обработки, px


def parse_int(value):
    """Целое число из строки формы или None (некорректное значение игнорируется)."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_date_str(value):
    """Дата YYYY-MM-DD из строки или None (некорректное значение игнорируется)."""
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def like_escape(text):
    """Экранирование спецсимволов LIKE: \\, % и _."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_filters(args, categories, places):
    """Условия WHERE из белого списка фрагментов; значения передаются параметрами.

    Возвращает словарь с фрагментами SQL, параметрами и введёнными значениями
    для подстановки обратно в форму.
    """
    conditions = ["items.status = 'active'"]
    params = []

    item_type = (args.get("type") or "").strip()
    if item_type not in ("lost", "found"):
        item_type = None
    else:
        conditions.append("items.type = ?")
        params.append(item_type)

    q = (args.get("q") or "").strip()
    if q:
        pattern = "%" + like_escape(q.lower()) + "%"
        conditions.append(
            "(PY_LOWER(items.title) LIKE ? ESCAPE '\\' "
            "OR PY_LOWER(items.description) LIKE ? ESCAPE '\\')"
        )
        params.extend([pattern, pattern])

    category_ids = [c["id"] for c in categories]
    category_id = parse_int(args.get("category_id"))
    if category_id not in category_ids:
        category_id = None
    else:
        conditions.append("items.category_id = ?")
        params.append(category_id)

    place_ids = [p["id"] for p in places]
    place_id = parse_int(args.get("place_id"))
    if place_id not in place_ids:
        place_id = None
    else:
        conditions.append("items.place_id = ?")
        params.append(place_id)

    date_from = parse_date_str(args.get("date"))
    date_str = args.get("date", "").strip() if date_from else ""
    if date_from:
        conditions.append("items.date >= ?")
        params.append(date_from.isoformat())

    has_filters = bool(item_type or q or category_id or place_id or date_from)
    return {
        "conditions": conditions,
        "params": params,
        "item_type": item_type,
        "q": q,
        "category_id": category_id,
        "place_id": place_id,
        "date": date_str,
        "has_filters": has_filters,
    }


def search_items(conn, filters, page_value):
    """Поиск по объявлениям с теми же условиями и пагинацией.

    Возвращает (объявления, данные пагинации). Общее количество считается
    отдельным запросом COUNT(*), затем LIMIT ? OFFSET ?.
    """
    where = " AND ".join(filters["conditions"])
    from_sql = (
        "FROM items "
        "JOIN categories ON categories.id = items.category_id "
        "JOIN places ON places.id = items.place_id "
        "WHERE " + where
    )
    total = conn.execute(
        "SELECT COUNT(*) AS n " + from_sql, filters["params"]
    ).fetchone()["n"]
    pages = max((total + PER_PAGE - 1) // PER_PAGE, 1)
    try:
        page = int(str(page_value).strip())
    except (TypeError, ValueError):
        page = 1
    page = min(max(page, 1), pages)

    items = conn.execute(
        "SELECT items.*, categories.name AS category_name, places.name AS place_name "
        + from_sql +
        " ORDER BY items.id DESC LIMIT ? OFFSET ?",
        filters["params"] + [PER_PAGE, (page - 1) * PER_PAGE],
    ).fetchall()

    # Параметры фильтров без page — чтобы ссылки на страницы сохраняли фильтры
    query_args = {}
    for key in ("type", "q", "category_id", "place_id", "date"):
        value = filters.get(key)
        if value not in (None, ""):
            query_args[key] = value

    pagination = {
        "page": page,
        "pages": pages,
        "total": total,
        "has_prev": page > 1,
        "has_next": page < pages,
        "args": query_args,
    }
    return items, pagination


def delete_photo(filename):
    """Удаляет сохранённый файл фото (например, если вставка в базу не удалась)."""
    if not filename:
        return
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        os.remove(path)
    except OSError:
        pass


def save_photo(file_storage):
    """Проверяет содержимое файла через Pillow и сохраняет фото.

    Имя и MIME-тип от клиента не доверяем: реальный формат определяем
    по содержимому. Возвращает (имя_файла | None, сообщение_об_ошибке | None).
    """
    if file_storage is None or not file_storage.filename:
        return None, None
    data = file_storage.read()
    if not data:
        return None, None

    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        with Image.open(BytesIO(data)) as img:
            real_format = img.format
    except (ValueError, UnidentifiedImageError, OSError):
        return None, "Допустимы только изображения JPEG, PNG и WebP"

    if real_format not in ALLOWED_PHOTO_FORMATS:
        return None, "Допустимы только изображения JPEG, PNG и WebP"

    # Повторно открываем файл, применяем EXIF-поворот и уменьшаем при необходимости
    try:
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            if max(img.size) > MAX_PHOTO_SIDE:
                img.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
            ext = ALLOWED_PHOTO_FORMATS[real_format]
            if ext == ".jpg" and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            filename = uuid.uuid4().hex + ext
            img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    except (ValueError, OSError):
        return None, "Не удалось обработать изображение, попробуйте другое"
    return filename, None


def validate_item_form(form, categories, places):
    """Проверка полей формы объявления, возвращает список ошибок на русском."""
    errors = []

    if form.get("type") not in ("lost", "found"):
        errors.append("Выберите тип объявления")

    title = form.get("title", "")
    if not 3 <= len(title) <= 100:
        errors.append("Введите название (от 3 до 100 символов)")

    description = form.get("description", "")
    if len(description) > 1000:
        errors.append("Описание не должно быть длиннее 1000 символов")

    category_id = parse_int(form.get("category_id"))
    if category_id is None or not any(c["id"] == category_id for c in categories):
        errors.append("Выберите категорию из списка")

    place_id = parse_int(form.get("place_id"))
    if place_id is None or not any(p["id"] == place_id for p in places):
        errors.append("Выберите место из списка")

    date_str = form.get("date", "")
    item_date = parse_date_str(date_str)
    if item_date is None:
        errors.append("Введите корректную дату")
    elif item_date > date.today():
        errors.append("Дата не может быть в будущем")

    return errors


# ------------------------------- Маршруты -------------------------------

@app.route("/")
def home():
    """Главная страница: первый экран и лента активных объявлений с пагинацией."""
    conn = get_db()
    filters = {"conditions": ["items.status = 'active'"], "params": []}
    items, pagination = search_items(conn, filters, request.args.get("page"))
    conn.close()
    return render_template("index.html", items=items, pag=pagination)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        contact = request.form.get("contact", "").strip()

        error = None
        if not name:
            error = "Введите имя."
        elif not email:
            error = "Введите email."
        elif "@" not in email or "." not in email:
            error = "Введите корректный email."
        elif not password:
            error = "Введите пароль."
        elif len(password) < 6:
            error = "Пароль должен быть не короче 6 символов."
        elif password != password2:
            # подтверждение пароля из формы регистрации вёрстки
            error = "Пароли не совпадают."

        if error is None:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (name, email, password_hash, contact) VALUES (?, ?, ?, ?)",
                    (name, email, generate_password_hash(password), contact or None),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                error = "Пользователь с таким email уже существует."
            finally:
                conn.close()

        if error is None:
            flash("Регистрация прошла успешно. Теперь войдите.", "success")
            return redirect(url_for("login"))
        flash(error, "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Введите email и пароль.", "danger")
        else:
            conn = get_db()
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()

            if row and check_password_hash(row["password_hash"], password):
                # «Запомнить меня» — чекбокс формы входа из вёрстки
                remember = request.form.get("remember") is not None
                login_user(User(row), remember=remember)
                next_page = request.args.get("next")
                return redirect(next_page if is_safe_next(next_page) else url_for("home"))

            # одно и то же сообщение для неверного email и неверного пароля
            flash("Неверный email или пароль.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    conn = get_db()
    try:
        categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        places = conn.execute("SELECT * FROM places ORDER BY name").fetchall()

        form = {"type": "", "title": "", "description": "",
                "category_id": "", "place_id": "", "date": ""}

        if request.method == "POST":
            for key in form:
                form[key] = (request.form.get(key) or "").strip()

            errors = validate_item_form(form, categories, places)

            # Фото обрабатываем только после проверки остальных полей
            photo_name = None
            if not errors:
                photo_name, photo_error = save_photo(request.files.get("photo"))
                if photo_error:
                    errors.append(photo_error)

            if not errors:
                try:
                    cur = conn.execute(
                        "INSERT INTO items (user_id, category_id, place_id, type, "
                        "title, description, date, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            current_user.id,
                            parse_int(form["category_id"]),
                            parse_int(form["place_id"]),
                            form["type"],
                            form["title"],
                            form["description"],
                            form["date"],
                            photo_name,
                        ),
                    )
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
                    delete_photo(photo_name)
                    errors.append("Не удалось сохранить объявление, попробуйте ещё раз")
                else:
                    flash("Объявление опубликовано", "success")
                    return redirect(url_for("item_detail", item_id=cur.lastrowid))

            for error in errors:
                flash(error, "danger")
        else:
            # На GET подставляем ?type=lost|found как предварительно выбранный тип
            form["type"] = request.args.get("type", "")
    finally:
        conn.close()

    return render_template("add.html", categories=categories, places=places, form=form)


@app.route("/items")
def items_list():
    """Списки «Пропажи» и «Находки» из вёрстки (lost.html / found.html).

    Поиск (q) и фильтры (category_id, place_id, date) — через GET-параметры,
    SQL — параметризованный, условия собираются из белого списка фрагментов.
    """
    item_type = "found" if request.args.get("type") == "found" else "lost"

    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    places = conn.execute("SELECT * FROM places ORDER BY name").fetchall()

    filters = build_filters(request.args, categories, places)
    # неизвестный тип игнорируем — показываем раздел «Пропажи» (как раньше)
    if not filters["item_type"]:
        filters["conditions"].append("items.type = ?")
        filters["params"].append(item_type)
        filters["item_type"] = item_type

    items, pagination = search_items(conn, filters, request.args.get("page"))
    conn.close()

    return render_template(
        "items.html",
        items=items, categories=categories, places=places,
        item_type=item_type, filters=filters, pag=pagination,
    )


@app.route("/uploads/<path:filename>")
def uploads(filename):
    """Выдача фотографий объявлений (поле items.photo).

    send_from_directory отдаёт файлы только из папки uploads/,
    попытка выйти за её пределы (например, /uploads/../app.py) даёт 404.
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    conn = get_db()
    item = conn.execute(
        "SELECT items.*, categories.name AS category_name, places.name AS place_name, "
        "users.name AS author_name, users.contact AS author_contact "
        "FROM items "
        "JOIN categories ON categories.id = items.category_id "
        "JOIN places ON places.id = items.place_id "
        "JOIN users ON users.id = items.user_id "
        "WHERE items.id = ?",
        (item_id,),
    ).fetchone()
    conn.close()
    if item is None:
        abort(404)
    return render_template("item_detail.html", item=item)


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    items = conn.execute(
        "SELECT items.*, categories.name AS category_name, places.name AS place_name "
        "FROM items "
        "JOIN categories ON categories.id = items.category_id "
        "JOIN places ON places.id = items.place_id "
        "WHERE items.user_id = ? "
        "ORDER BY items.id DESC",
        (current_user.id,),
    ).fetchall()
    conn.close()
    active = [i for i in items if i["status"] == "active"]
    closed = [i for i in items if i["status"] == "closed"]

    # Счётчики статистики профиля из вёрстки (все — из базы, без заглушек)
    matches_conn = get_db()
    matches = matches_conn.execute(
        "SELECT COUNT(*) AS n FROM matches "
        "JOIN items AS lost ON lost.id = matches.lost_item_id "
        "JOIN items AS found ON found.id = matches.found_item_id "
        "WHERE lost.user_id = ? OR found.user_id = ?",
        (current_user.id, current_user.id),
    ).fetchone()["n"]
    matches_conn.close()

    stats = {
        "total": len(items),
        "found": sum(1 for i in items if i["type"] == "found"),
        "matches": matches,
    }
    return render_template("dashboard.html", active=active, closed=closed, stats=stats)


@app.route("/item/<int:item_id>/close", methods=["POST"])
@login_required
def close_item(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        conn.close()
        abort(404)
    if item["user_id"] != current_user.id:  # закрыть можно только своё объявление
        conn.close()
        abort(403)
    conn.execute("UPDATE items SET status = 'closed' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Объявление закрыто.", "success")
    return redirect(url_for("dashboard"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def request_too_large(error):
    flash("Файл слишком большой, максимум 5 МБ", "danger")
    return redirect(url_for("add"))


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
