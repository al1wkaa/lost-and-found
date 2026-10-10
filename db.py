import sqlite3

DB_NAME = "lostfound.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # чтобы обращаться к полям по имени
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

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('lost', 'found')),
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        place TEXT NOT NULL,
        date TEXT NOT NULL,
        photo TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_item_id INTEGER NOT NULL,
        found_item_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'new',
        FOREIGN KEY (lost_item_id) REFERENCES items (id),
        FOREIGN KEY (found_item_id) REFERENCES items (id)
    );
    """)
    conn.commit()
    conn.close()