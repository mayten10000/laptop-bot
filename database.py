import sqlite3

def init_db():
    conn = sqlite3.connect("laptop_search.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_search(user_id, query):
    conn = sqlite3.connect("laptop_search.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO search_history (user_id, query) VALUES (?, ?)", (user_id, query))
    conn.commit()
    conn.close()

def get_search_history(user_id):
    conn = sqlite3.connect("laptop_search.db")
    cursor = conn.cursor()
    cursor.execute("SELECT query FROM search_history WHERE user_id = ?", (user_id, ))
    rows = cursor.fetchall()
    conn.close()

    return [{"query": row[0]} for row in rows]
