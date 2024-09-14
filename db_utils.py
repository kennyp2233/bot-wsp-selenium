import sqlite3

def create_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = sqlite3.connect('user_state.db')
    return conn

def initialize_database():
    """Inicializa la base de datos y crea la tabla 'users' si no existe."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        phone_number TEXT PRIMARY KEY,
        state TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

async def get_user_state(user):
    """Obtiene el estado de un usuario dado su número de teléfono."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM users WHERE phone_number = ?", (user,))
    state = cursor.fetchone()
    conn.close()
    return state[0] if state else None

async def save_user_state(user, state):
    """Guarda el estado de un usuario dado su número de teléfono."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (phone_number, state) VALUES (?, ?)", (user, state))
    conn.commit()
    conn.close()

# Inicializa la base de datos y crea la tabla 'users' si no existe
initialize_database()
