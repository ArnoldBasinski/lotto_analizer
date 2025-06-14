import sqlite3

# Połączenie do pliku bazy danych (utworzy plik, jeśli nie istnieje)
conn = sqlite3.connect("lotto.db")
cursor = conn.cursor()

# Tworzenie tabeli, jeśli jeszcze nie istnieje
cursor.execute("""
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
conn.close()

print("✅ Tabela 'losowania' utworzona w lotto.db")