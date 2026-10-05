import sqlite3

# Función para conectar o crear la base de datos local
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Lee y ejecuta el archivo schema.sql que creamos recién
    with open("schema.sql", "r") as f:
        cursor.executescript(f.read())
        
    conn.commit()
    conn.close()
    print("¡Base de datos creada con éxito!")

if __name__ == "__main__":
    init_db()