import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db, init_db

app = Flask(__name__)
# Секретный ключ подписывает сессии. На хостинге задайте свой через переменную окружения SECRET_KEY.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
init_db()

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Войдите, чтобы открыть эту страницу."
login_manager.login_message_category = "warning"


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


@app.route("/")
def home():
    conn = get_db()
    items = conn.execute(
        "SELECT items.*, categories.name AS category_name, places.name AS place_name "
        "FROM items "
        "JOIN categories ON categories.id = items.category_id "
        "JOIN places ON places.id = items.place_id "
        "WHERE items.status = 'active' "
        "ORDER BY items.id DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", items=items)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        contact = request.form["contact"].strip()

        error = None
        if not name:
            error = "Введите имя."
        elif "@" not in email or "." not in email:
            error = "Введите корректный email."
        elif len(password) < 6:
            error = "Пароль должен быть не короче 6 символов."

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
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if row and check_password_hash(row["password_hash"], password):
            login_user(User(row))
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
    if request.method == "POST":
        conn.execute(
            "INSERT INTO items (user_id, category_id, place_id, type, title, description, date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                current_user.id,  # реальный автор объявления
                request.form["category_id"],
                request.form["place_id"],
                request.form["type"],
                request.form["title"],
                request.form["description"],
                request.form["date"],
            ),
        )
        conn.commit()
        conn.close()
        flash("Объявление опубликовано.", "success")
        return redirect(url_for("home"))

    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    places = conn.execute("SELECT * FROM places ORDER BY name").fetchall()
    conn.close()
    return render_template("add.html", categories=categories, places=places)

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
    return render_template("dashboard.html", active=active, closed=closed)


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


if __name__ == "__main__":
    app.run(debug=True)