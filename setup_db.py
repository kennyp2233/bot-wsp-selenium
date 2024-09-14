import sqlite3

def setup_database():
    conn = sqlite3.connect('user_state.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            state TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
