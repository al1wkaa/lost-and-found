from flask import Flask, render_template, request, redirect, url_for
from db import get_db, init_db

app = Flask(__name__)
init_db()


@app.route("/")
def home():
    conn = get_db()
    items = conn.execute(
        "SELECT items.*, categories.name AS category_name, places.name AS place_name "
        "FROM items "
        "JOIN categories ON categories.id = items.category_id "
        "JOIN places ON places.id = items.place_id "
        "ORDER BY items.id DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", items=items)


@app.route("/add", methods=["GET", "POST"])
def add():
    conn = get_db()
    if request.method == "POST":
        conn.execute(
            "INSERT INTO items (user_id, category_id, place_id, type, title, description, date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                1,  # временно, пока нет регистрации
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
        return redirect(url_for("home"))

    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    places = conn.execute("SELECT * FROM places ORDER BY name").fetchall()
    conn.close()
    return render_template("add.html", categories=categories, places=places)


if __name__ == "__main__":
    app.run(debug=True)