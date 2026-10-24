import sqlite3

DB_NAME = "lostfound.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        contact TEXT
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS places (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS place_neighbors (
        place_id INTEGER NOT NULL,
        neighbor_id INTEGER NOT NULL,
        PRIMARY KEY (place_id, neighbor_id),
        FOREIGN KEY (place_id) REFERENCES places (id),
        FOREIGN KEY (neighbor_id) REFERENCES places (id)
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        place_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('lost', 'found')),
        title TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        photo TEXT,
        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (place_id) REFERENCES places (id)
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_item_id INTEGER NOT NULL,
        found_item_id INTEGER NOT NULL,
        score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
        status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'confirmed', 'rejected')),
        UNIQUE (lost_item_id, found_item_id),
        FOREIGN KEY (lost_item_id) REFERENCES items (id),
        FOREIGN KEY (found_item_id) REFERENCES items (id)
    );
    """)
    seed(conn)
    conn.commit()
    conn.close()


def seed(conn):
    """Начальные данные справочников (повторный запуск ничего не дублирует)."""
    categories = ["Наушники", "Телефон", "Ключи", "Документы", "Одежда", "Другое"]
    places = ["Кафе", "Библиотека", "Главный корпус", "Общежитие", "Спортзал", "Остановка"]
    neighbors = [("Кафе", "Главный корпус"), ("Главный корпус", "Библиотека"),
                 ("Общежитие", "Спортзал"), ("Остановка", "Общежитие")]

    for c in categories:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (c,))
    for p in places:
        conn.execute("INSERT OR IGNORE INTO places (name) VALUES (?)", (p,))
    for a, b in neighbors:
        # связь в обе стороны: если A рядом с B, то и B рядом с A
        for x, y in ((a, b), (b, a)):
            conn.execute(
                "INSERT OR IGNORE INTO place_neighbors (place_id, neighbor_id) "
                "SELECT p1.id, p2.id FROM places p1, places p2 WHERE p1.name = ? AND p2.name = ?",
                (x, y),
            )