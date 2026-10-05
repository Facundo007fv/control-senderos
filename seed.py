import sqlite3
import os

DB_NAME = "database.db"
SCHEMA_FILE = "schema.sql"

def init_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("🗑️ Base de datos anterior eliminada.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        print("📐 Esquema creado con éxito.")
    else:
        print("⚠️ No se encontró schema.sql")
        return

    # Cuenta SuperAdmin por defecto
    cursor.execute("""
        INSERT OR IGNORE INTO admins (id, username, password, park_id, is_super) 
        VALUES (999, 'facu_master', 'trail2026', NULL, 1)
    """)

    conn.commit()
    conn.close()
    print("🌲 ¡Base de datos inicializada correctamente!")

if __name__ == "__main__":
    init_db()