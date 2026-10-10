from flask import Flask, render_template, request, redirect, url_for
from db import get_db, init_db

app = Flask(__name__)
init_db()

@app.route("/")
def home():
    conn = get_db()
    items = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", items=items)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        item_type = request.form["type"]
        category = request.form["category"]
        title = request.form["title"]
        description = request.form["description"]
        place = request.form["place"]
        date = request.form["date"]

        conn = get_db()
        # user_id=1 временно, пока нет регистрации
        conn.execute(
            "INSERT INTO items (user_id, type, category, title, description, place, date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, item_type, category, title, description, place, date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)