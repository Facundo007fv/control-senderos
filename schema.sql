-- Tabla de Parques / Reservas (Gestionado por los dueños - B2B)
CREATE TABLE IF NOT EXISTS parks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    max_capacity INTEGER DEFAULT 100, -- Aforo máximo permitido
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Senderos / Recorridos (Un parque puede tener muchos senderos)
CREATE TABLE IF NOT EXISTS trails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    park_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    difficulty TEXT NOT NULL, -- Ej: Fácil, Moderado, Difícil
    qr_code TEXT UNIQUE NOT NULL, -- Código único para el QR del sendero
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    is_open BOOLEAN DEFAULT 1, -- Estado del sendero (Abierto/Cerrado por clima)
    FOREIGN KEY (park_id) REFERENCES parks (id) ON DELETE CASCADE
);

-- Tabla de Check-ins y Registros de Runners (B2C)
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trail_id INTEGER NOT NULL,
    runner_name TEXT NOT NULL,
    runner_phone TEXT NOT NULL,
    companions_count INTEGER DEFAULT 0, -- Cantidad de acompañantes (ej: hijos)
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP NULL, -- Se completa al salir
    status TEXT DEFAULT 'active', -- 'active', 'completed', 'emergency'
    sos_active BOOLEAN DEFAULT 0, -- Botón de emergencia activado (1 = Sí, 0 = No)
    last_latitude REAL NULL, -- Ubicación en vivo para emergencias
    last_longitude REAL NULL,
    FOREIGN KEY (trail_id) REFERENCES trails (id) ON DELETE CASCADE
);