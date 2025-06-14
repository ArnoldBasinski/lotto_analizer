import sqlite3
from datetime import datetime

DB_FILE = "lotto.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS losowania (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            l1 INTEGER,
            l2 INTEGER,
            l3 INTEGER,
            l4 INTEGER,
            l5 INTEGER,
            l6 INTEGER
        );
        """)
        conn.commit()

def zapisz_wyniki_do_bazy(wyniki, daty=None):
    """
    Nadpisuje zawartość tabeli losowania.
    """
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # ❌ Usuń wszystkie poprzednie wpisy
        c.execute("DELETE FROM losowania")

        for i, w in enumerate(wyniki):
            if len(w) != 6:
                continue
            data = daty[i] if daty else datetime.now().strftime("%Y-%m-%d")
            c.execute("""
                INSERT INTO losowania (data, l1, l2, l3, l4, l5, l6)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data, *w))
        conn.commit()

def pobierz_wszystkie_wyniki():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT l1, l2, l3, l4, l5, l6 FROM losowania ORDER BY id")
        wyniki = c.fetchall()
    return [list(w) for w in wyniki]
