-- Tabla de Parques / Reservas (B2B)
CREATE TABLE IF NOT EXISTS parks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    cuit TEXT UNIQUE,
    latitude TEXT,
    longitude TEXT,
    max_capacity INTEGER DEFAULT 100,
    open_time TEXT DEFAULT '08:00',
    close_time TEXT DEFAULT '18:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_paid INTEGER DEFAULT 0
);

-- Tabla de Administradores
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    park_id INTEGER,
    is_super INTEGER DEFAULT 0,
    FOREIGN KEY (park_id) REFERENCES parks (id) ON DELETE CASCADE
);

-- Tabla de Senderos
CREATE TABLE IF NOT EXISTS trails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    park_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    is_open BOOLEAN DEFAULT 1,
    route_points TEXT,
    FOREIGN KEY (park_id) REFERENCES parks (id) ON DELETE CASCADE
);

-- Tabla de Check-ins y Registros (B2C)
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trail_id INTEGER NOT NULL,
    runner_name TEXT NOT NULL,
    runner_phone TEXT NOT NULL,
    companions_count INTEGER DEFAULT 0,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP NULL,
    status TEXT DEFAULT 'active',
    sos_active BOOLEAN DEFAULT 0,
    latitude TEXT,
    longitude TEXT,
    FOREIGN KEY (trail_id) REFERENCES trails (id) ON DELETE CASCADE
);

-- Tabla de Buzón de Sugerencias
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    park_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (park_id) REFERENCES parks (id) ON DELETE CASCADE
);