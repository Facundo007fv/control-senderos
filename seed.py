import sqlite3
import os

DB_NAME = "database.db"
SCHEMA_FILE = "schema.sql"

def init_db():
    # Si ya existía una base de datos vieja, la eliminamos para evitar conflictos
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("🗑️ Base de datos anterior eliminada.")

    # Conectamos (esto creará un nuevo archivo database.db vacío)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Leemos y ejecutamos el archivo schema.sql para crear las tablas nuevas
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_script = f.read()
        cursor.executescript(schema_script)
        print("📐 Esquema de base de datos creado exitosamente desde schema.sql.")
    else:
        print("⚠️ No se encontró el archivo schema.sql. Asegúrate de tenerlo en la carpeta.")
        return

    # Insertamos Parques de prueba (Ej: En las sierras de Córdoba)
    parks_data = [
        ("Parque Nacional Quebrada del Condorito", "Córdoba, Argentina", -31.6167, -64.7167, 150),
        ("Reserva Natural Cerro Uritorco", "Capilla del Monte, Córdoba", -30.8500, -64.4667, 200),
        ("Parque Estancia La Candelaria", "Sierras de Córdoba", -31.4500, -64.8000, 100)
    ]
    
    cursor.executemany("""
        INSERT INTO parks (name, location, latitude, longitude, max_capacity)
        VALUES (?, ?, ?, ?, ?)
    """, parks_data)
    
    conn.commit()

    # Recuperamos los IDs de los parques recién creados para asociarles senderos
    cursor.execute("SELECT id, name FROM parks")
    parks = cursor.fetchall()

    # Insertamos Senderos múltiples por cada parque con sus respectivos códigos QR
    trails_data = []
    for park_id, park_name in parks:
        if "Condorito" in park_name:
            trails_data.extend([
                (park_id, "Sendero Balcón Norte", "Moderado", "QR-CONDORITO-01", -31.6150, -64.7150, 1),
                (park_id, "Bajada a la Quebrada", "Difícil", "QR-CONDORITO-02", -31.6180, -64.7180, 1)
            ])
        elif "Uritorco" in park_name:
            trails_data.extend([
                (park_id, "Ascenso Principal Cima", "Difícil", "QR-URITORCO-01", -30.8520, -64.4680, 1),
                (park_id, "Sendero de los Minerales", "Fácil", "QR-URITORCO-02", -30.8480, -64.4650, 1)
            ])
        else:
            trails_data.append(
                (park_id, "Circuito Histórico Jesuítico", "Fácil", "QR-CANDELARIA-01", -31.4520, -64.8020, 1)
            )

    cursor.executemany("""
        INSERT INTO trails (park_id, name, difficulty, qr_code, latitude, longitude, is_open)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, trails_data)

    conn.commit()
    conn.close()
    print("🌲 ¡Base de datos poblada con éxito con parques, senderos y códigos QR!")

if __name__ == "__main__":
    init_db()