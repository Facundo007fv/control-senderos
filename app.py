from flask import Flask, render_template_string, request, redirect, url_for, session, Response
import sqlite3
import json
import os
import io
import qrcode
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura_trail_control"

try:
    import mercadopago
    # Reemplazá con tu Access Token real de Mercado Pago
    sdk = mercadopago.SDK("TEST-tu-access-token-de-mercado-pago-aqui")
except ImportError:
    sdk = None

translations = {
    "es": {
        "title": "Control de Senderos & Montaña",
        "subtitle": "Monitoreo inteligente, seguridad en vivo y gestión de rutas al aire libre para parques y reservas naturales.",
        "lang_switch": "Switch to English",
        "badge": "SaaS de Seguridad en Montaña",
        "btn_admin": "🛡️ Acceso Administradores",
        "btn_register_park": "🌲 Registrar mi Parque",
        "instructions_title": "📖 Guía e Instrucciones de Uso",
        "admin_guide_title": "Para Propietarios y Administradores (B2B)",
        "admin_step1": "1. Registra tu establecimiento con tu CUIT: ¡Disfrutas de 7 días de prueba completamente gratis!",
        "admin_step2": "2. Accede a tu panel privado para gestionar senderos, grabarlos por GPS y configurar aforo en vivo.",
        "admin_step3": "3. Imprime el código QR único de la entrada principal para que los visitantes se registren al instante.",
        "admin_step4": "4. Finalizada la semana de prueba, elige tu plan mensual, semestral o anual para mantener la app activa.",
        "runner_guide_title": "Para Visitantes y Senderistas (B2C)",
        "runner_step1": "1. Escanea con la cámara de tu celular el código QR ubicado en el ingreso del parque.",
        "runner_step2": "2. Selecciona el sendero por el cual deseas realizar tu recorrido y completa tus datos de contacto.",
        "runner_step3": "3. Utiliza el cronómetro en vivo para medir tu rendimiento y mantén activo el botón de emergencia (SOS).",
        "runner_step4": "4. Al finalizar el trayecto, presiona el botón de Check-out para registrar tu salida de manera segura.",
        "disclaimer_title": "⚖️ Descargo de Responsabilidad (Disclaimer Legal)",
        "disclaimer_text": "TrailControl es una herramienta tecnológica de software orientada a facilitar la gestión de aforos, el registro de ingresos y el monitoreo de senderos. La plataforma no sustituye los servicios de rescate profesionales, la señalización física en terreno, ni la responsabilidad individual de los visitantes sobre su propia seguridad y estado físico. Los propietarios y administradores del parque o reserva son los únicos responsables de la seguridad del predio, la verificación de los estados climáticos y la coordinación de los protocolos de emergencia locales ante incidentes.",
        "diff_facil": "Fácil",
        "diff_moderado": "Moderado",
        "diff_dificil": "Difícil",
        "status_open": "Abierto (OK)",
        "status_closed": "Cerrado",
        "btn_checkin": "Hacer Check-in",
        "select_trail": "Seleccioná tu Sendero",
        "difficulty": "Dificultad",
        "closed_weather": "Cerrado por Clima",
        "back_home": "Volver al inicio",
        "operating_hours": "Horario operativo",
        "checkin_title": "Check-in de Seguridad",
        "checkin_subtitle": "Registro de Ingreso",
        "back_trail": "Volver al sendero",
        "name_label": "Nombre y Apellido",
        "phone_label": "Teléfono de Emergencia / Celular",
        "companions_label": "Cantidad de Acompañantes",
        "start_button": "Iniciar Recorrido"
    },
    "en": {
        "title": "Trail & Mountain Control",
        "subtitle": "Smart monitoring, live safety, and outdoor route management for parks and natural reserves.",
        "lang_switch": "Cambiar a Español",
        "badge": "Mountain Safety SaaS",
        "btn_admin": "🛡️ Admin Login",
        "btn_register_park": "🌲 Register my Park",
        "instructions_title": "📖 User Guide & Instructions",
        "admin_guide_title": "For Park Owners & Administrators (B2B)",
        "admin_step1": "1. Register your property with your Tax ID/CUIT: Enjoy a 7-day completely free trial!",
        "admin_step2": "2. Access your private dashboard to manage trails, record GPS routes, and set live capacity.",
        "admin_step3": "3. Print your unique main entrance QR code for instant visitor registration.",
        "admin_step4": "4. After the trial week, choose your monthly, 6-month, or annual plan to keep the app active.",
        "runner_guide_title": "For Visitors & Hikers (B2C)",
        "runner_step1": "1. Scan the QR code located at the park entrance using your phone camera.",
        "runner_step2": "2. Select the trail you wish to hike and enter your emergency contact details.",
        "runner_step3": "3. Use the live timer to track your performance and keep the SOS emergency button ready.",
        "runner_step4": "4. Once finished, click the Check-out button to safely record your exit.",
        "disclaimer_title": "⚖️ Disclaimer of Liability",
        "disclaimer_text": "TrailControl is a software technology tool designed to facilitate capacity management, visitor registration, and trail monitoring. The platform does not replace professional rescue services, physical terrain signage, or visitors' individual responsibility for their own safety and physical condition. Park or reserve owners and administrators are solely responsible for site security, weather verification, and coordinating local emergency protocols during incidents.",
        "diff_facil": "Easy",
        "diff_moderado": "Moderate",
        "diff_dificil": "Hard",
        "status_open": "Open (OK)",
        "status_closed": "Closed",
        "btn_checkin": "Check-in",
        "select_trail": "Select your Trail",
        "difficulty": "Difficulty",
        "closed_weather": "Closed due to Weather",
        "back_home": "Back to Home",
        "operating_hours": "Operating hours",
        "checkin_title": "Safety Check-in",
        "checkin_subtitle": "Visitor Registration",
        "back_trail": "Back to trail",
        "name_label": "Full Name",
        "phone_label": "Emergency Phone / Mobile",
        "companions_label": "Number of Companions",
        "start_button": "Start Hike"
    }
}

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
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
        )
    ''')

    try:
        cursor.execute("ALTER TABLE parks ADD COLUMN cuit TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE parks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE parks ADD COLUMN is_paid INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            park_id INTEGER,
            is_super INTEGER DEFAULT 0,
            FOREIGN KEY (park_id) REFERENCES parks (id)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE admins ADD COLUMN is_super INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Creamos tu cuenta global de SuperAdmin (facu_master / trail2026)
    cursor.execute("""
        INSERT OR IGNORE INTO admins (id, username, password, park_id, is_super) 
        VALUES (999, 'facu_master', 'trail2026', NULL, 1)
    """)
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            park_id INTEGER,
            name TEXT NOT NULL,
            difficulty TEXT,
            is_open INTEGER DEFAULT 1,
            route_points TEXT,
            FOREIGN KEY (park_id) REFERENCES parks (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trail_id INTEGER,
            runner_name TEXT NOT NULL,
            runner_phone TEXT NOT NULL,
            companions_count INTEGER DEFAULT 0,
            check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            check_out_time TIMESTAMP NULL,
            status TEXT DEFAULT 'active',
            sos_active INTEGER DEFAULT 0,
            latitude TEXT,
            longitude TEXT,
            FOREIGN KEY (trail_id) REFERENCES trails (id)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE registrations ADD COLUMN latitude TEXT")
        cursor.execute("ALTER TABLE registrations ADD COLUMN longitude TEXT")
    except sqlite3.OperationalError:
        pass

    # Tabla para el buzón de sugerencias y mejoras de los parques
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            park_id INTEGER,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (park_id) REFERENCES parks (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def generate_qr_base64(data_text):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.route("/")
def home():
    lang = request.args.get("lang", "es")
    if lang not in translations:
        lang = "es"
        
    t = translations[lang]
    other_lang = "en" if lang == "es" else "es"

    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{t['title']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen text-slate-100 font-sans selection:bg-emerald-500 selection:text-white flex flex-col justify-between">
        <header class="bg-slate-900/70 backdrop-blur-xl border-b border-emerald-500/10 sticky top-0 z-50 shadow-lg">
            <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="bg-emerald-600 p-2.5 rounded-2xl shadow-md text-xl">🏔️</div>
                    <span class="font-black text-xl tracking-tight text-white">Trail<span class="text-emerald-400">Control</span></span>
                </div>
                <div class="flex items-center gap-3 flex-wrap">
                    <a href="/register-park" class="text-xs font-bold text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-500/30 px-4 py-2.5 rounded-xl transition shadow-sm">
                        {t['btn_register_park']}
                    </a>
                    <a href="/login" class="text-xs font-bold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2.5 rounded-xl transition shadow-sm">
                        {t['btn_admin']}
                    </a>
                    <a href="/?lang={other_lang}" class="text-xs font-bold text-emerald-300 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/20 px-4 py-2.5 rounded-xl transition">
                        🌐 {t['lang_switch']}
                    </a>
                </div>
            </div>
        </header>

        <main class="max-w-6xl mx-auto px-6 py-12 w-full">
            <div class="mb-12 bg-gradient-to-r from-emerald-900/30 via-slate-900/50 to-slate-900/20 p-8 md:p-14 rounded-3xl border border-emerald-500/20 shadow-2xl backdrop-blur-md text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-8">
                <div>
                    <span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-bold px-3.5 py-1 rounded-full uppercase tracking-wider mb-4 inline-block">{t['badge']}</span>
                    <h1 class="text-3xl md:text-5xl font-black mb-4 text-white tracking-tight">{t['title']}</h1>
                    <p class="text-base md:text-lg text-slate-300 max-w-2xl font-normal leading-relaxed">{t['subtitle']}</p>
                </div>
                <div class="flex flex-col gap-3 min-w-[220px]">
                    <a href="/register-park" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-2xl shadow-lg transition text-center text-sm flex items-center justify-center gap-2">
                        <span>🎁</span> ¡7 Días Gratis!
                    </a>
                    <a href="/login" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold py-3.5 px-6 rounded-2xl border border-slate-700 transition text-center text-sm">
                        🛡️ Iniciar Sesión Admin
                    </a>
                </div>
            </div>

            <section class="bg-slate-900/60 border border-slate-800 p-8 md:p-12 rounded-3xl shadow-xl backdrop-blur-md mb-12">
                <h2 class="text-2xl font-black text-white mb-8 flex items-center gap-3">
                    <span class="bg-emerald-700 p-2.5 rounded-2xl text-base shadow-sm">📖</span> {t['instructions_title']}
                </h2>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="bg-slate-950/80 p-6 md:p-8 rounded-2xl border border-slate-800 flex flex-col justify-between">
                        <div>
                            <span class="bg-emerald-500/20 text-emerald-400 font-bold text-[10px] px-3 py-1 rounded-full uppercase tracking-wider inline-block mb-3">B2B - Establecimientos ($34.000/mes)</span>
                            <h3 class="text-xl font-black text-white mb-4">{t['admin_guide_title']}</h3>
                            <ul class="space-y-3 text-sm text-slate-300">
                                <li class="flex items-start gap-2.5"><span>✅</span> {t['admin_step1']}</li>
                                <li class="flex items-start gap-2.5"><span>✅</span> {t['admin_step2']}</li>
                                <li class="flex items-start gap-2.5"><span>✅</span> {t['admin_step3']}</li>
                                <li class="flex items-start gap-2.5"><span>✅</span> {t['admin_step4']}</li>
                            </ul>
                        </div>
                        <div class="mt-6 pt-4 border-t border-slate-800/80">
                            <a href="/register-park" class="text-xs font-bold text-emerald-400 hover:underline">Comenzar 7 días gratis →</a>
                        </div>
                    </div>

                    <div class="bg-slate-950/80 p-6 md:p-8 rounded-2xl border border-slate-800 flex flex-col justify-between">
                        <div>
                            <span class="bg-blue-500/20 text-blue-400 font-bold text-[10px] px-3 py-1 rounded-full uppercase tracking-wider inline-block mb-3">B2C - Senderistas (Gratis)</span>
                            <h3 class="text-xl font-black text-white mb-4">{t['runner_guide_title']}</h3>
                            <ul class="space-y-3 text-sm text-slate-300">
                                <li class="flex items-start gap-2.5"><span>🥾</span> {t['runner_step1']}</li>
                                <li class="flex items-start gap-2.5"><span>🥾</span> {t['runner_step2']}</li>
                                <li class="flex items-start gap-2.5"><span>🥾</span> {t['runner_step3']}</li>
                                <li class="flex items-start gap-2.5"><span>🥾</span> {t['runner_step4']}</li>
                            </ul>
                        </div>
                        <div class="mt-6 pt-4 border-t border-slate-800/80">
                            <span class="text-xs text-slate-500">Acceso exclusivo mediante QR en destino.</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <footer class="bg-slate-950 border-t border-slate-900 py-8 px-6 mt-12 text-slate-400 text-xs">
            <div class="max-w-6xl mx-auto space-y-3">
                <div class="font-bold text-slate-300 flex items-center gap-2">
                    <span>{t['disclaimer_title']}</span>
                </div>
                <p class="leading-relaxed text-slate-500 text-[11px]">
                    {t['disclaimer_text']}
                </p>
                <div class="pt-4 border-t border-slate-900 flex flex-col md:flex-row justify-between items-center gap-2 text-[11px] text-slate-600">
                    <p>© 2026 TrailControl. Todos los derechos reservados.</p>
                    <p>Plataforma SaaS de Control y Seguridad en Entornos Naturales.</p>
                </div>
            </div>
        </footer>
    </body>
    </html>
    """

@app.route("/register-park", methods=["GET", "POST"])
def register_park():
    error = ""
    if request.method == "POST":
        park_name = request.form.get("park_name")
        location = request.form.get("location")
        cuit = request.form.get("cuit")
        terms = request.form.get("terms")
        latitude = request.form.get("latitude", "-31.4201")
        longitude = request.form.get("longitude", "-64.4988")
        max_capacity = request.form.get("max_capacity", 100)
        open_time = request.form.get("open_time", "08:00")
        close_time = request.form.get("close_time", "18:00")
        
        username = request.form.get("username")
        password = request.form.get("password")

        if not terms:
            error = "⚠️ Debes aceptar los Términos y Condiciones y el Descargo de Responsabilidad para continuar."
        else:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO parks (name, location, cuit, latitude, longitude, max_capacity, open_time, close_time, is_paid)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (park_name, location, cuit, latitude, longitude, max_capacity, open_time, close_time))
                park_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO admins (username, password, park_id, is_super)
                    VALUES (?, ?, ?, 0)
                """, (username, password, park_id))

                conn.commit()
                conn.close()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError as e:
                conn.close()
                if "cuit" in str(e).lower():
                    error = "⚠️ Este CUIT ya registró un parque anteriormente y no puede reclamar otra prueba gratuita. Contacte a soporte para adquirir el servicio ($34.000/mes)."
                else:
                    error = "El nombre de usuario de administrador ya existe o el CUIT ya fue utilizado."

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Registrar Parque - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen flex items-center justify-center p-6 text-slate-100 selection:bg-emerald-500 selection:text-white">
        <div class="bg-slate-900/95 backdrop-blur-xl p-8 rounded-3xl shadow-2xl max-w-lg w-full border border-slate-800">
            <div class="text-center mb-6">
                <span class="bg-emerald-500/20 text-emerald-300 text-[10px] font-black px-3.5 py-1 rounded-full uppercase tracking-wider border border-emerald-500/30 inline-block mb-2">SaaS B2B • 7 Días Gratis</span>
                <h2 class="text-2xl font-black text-white tracking-tight">Registra tu Establecimiento</h2>
                <p class="text-xs text-slate-400 mt-1">Completa los datos fiscales y de acceso para comenzar tu prueba.</p>
            </div>
            
            {f'<div class="bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-bold p-4 rounded-2xl mb-6 text-center leading-relaxed">{error}</div>' if error else ''}

            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Nombre del Parque / Reserva</label>
                    <input type="text" name="park_name" required placeholder="Ej: Reserva Ecológica Los Gigantes" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Ubicación / Ciudad</label>
                    <input type="text" name="location" required placeholder="Ej: Punilla, Córdoba" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">CUIT del Establecimiento (Anti-Fraude)</label>
                    <input type="text" name="cuit" required placeholder="Ej: 30-71234567-8" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono">
                    <span class="text-[10px] text-slate-500 mt-1 block">Requerido para validar la identidad y evitar registros duplicados de prueba.</span>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Usuario Admin B2B</label>
                        <input type="text" name="username" required placeholder="Ej: admin_gigantes" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Contraseña</label>
                        <input type="password" name="password" required placeholder="••••" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                    </div>
                </div>
                
                <div class="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 text-[11px] text-slate-400 space-y-2">
                    <div class="flex items-start gap-2.5">
                        <input type="checkbox" name="terms" value="accepted" required class="mt-0.5 accent-emerald-500">
                        <label class="leading-relaxed">
                            Acepto los <strong>Términos y Condiciones</strong>. Comprendo que TrailControl es una plataforma tecnológica de gestión y que la responsabilidad legal sobre la seguridad física del predio, señalización y coordinación de rescates recae exclusivamente sobre el establecimiento.
                        </label>
                    </div>
                </div>

                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black py-4 px-4 rounded-xl transition shadow-lg shadow-emerald-950/50 mt-4 text-sm">
                    🚀 Iniciar 7 Días Gratis
                </button>
            </form>
            
            <div class="mt-6 text-center">
                <a href="/" class="text-xs font-bold text-slate-400 hover:text-white transition">← Volver al inicio</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, park_id, is_super FROM admins WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin_id"] = admin[0]
            session["park_id"] = admin[1]
            session["is_super"] = admin[2]
            
            if admin[2] == 1:
                return redirect(url_for("superadmin_panel"))
            
            return redirect(url_for("admin_panel"))
        else:
            error = "Usuario o contraseña incorrectos."

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Admin - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen flex items-center justify-center p-6 selection:bg-emerald-500 selection:text-white">
        <div class="bg-white/95 backdrop-blur-xl p-8 rounded-3xl shadow-2xl max-w-md w-full text-slate-800 border border-emerald-900/10">
            <div class="text-center mb-6">
                <div class="inline-block bg-emerald-700 text-white p-3 rounded-2xl text-2xl shadow-md mb-3">🛡️</div>
                <h2 class="text-2xl font-black text-slate-900 tracking-tight">Acceso Administradores</h2>
                <p class="text-xs text-slate-500 mt-1">Ingresa con tus credenciales asignadas</p>
            </div>
            
            {f'<div class="bg-rose-100 text-rose-700 text-xs font-bold p-3.5 rounded-xl mb-4 text-center shadow-xs">{error}</div>' if error else ''}

            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1.5">Usuario</label>
                    <input type="text" name="username" required placeholder="Ej: admin_condorito" class="w-full bg-slate-100/80 border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 transition">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1.5">Contraseña</label>
                    <input type="password" name="password" required placeholder="••••" class="w-full bg-slate-100/80 border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 transition">
                </div>
                <button type="submit" class="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3.5 px-4 rounded-xl transition shadow-lg mt-2">
                    Ingresar al Panel
                </button>
            </form>
            
            <div class="mt-6 text-center">
                <a href="/" class="text-xs font-bold text-slate-500 hover:text-slate-800 transition">← Volver al inicio</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/feedback", methods=["POST"])
def admin_feedback():
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))
    
    park_id = session["park_id"]
    message = request.form.get("message")
    
    if message:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (park_id, message) VALUES (?, ?)", (park_id, message))
        conn.commit()
        conn.close()
        
    return redirect(url_for("admin_panel") + "?sent=true")

@app.route("/superadmin")
def superadmin_panel():
    if not session.get("is_super"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Consultamos parques
    cursor.execute("""
        SELECT parks.id, parks.name, parks.location, parks.cuit, parks.created_at, parks.is_paid, admins.username
        FROM parks LEFT JOIN admins ON parks.id = admins.park_id WHERE admins.is_super = 0
    """)
    parks = cursor.fetchall()

    # Consultamos sugerencias del buzón con el nombre del parque
    cursor.execute("""
        SELECT feedback.message, feedback.created_at, parks.name 
        FROM feedback JOIN parks ON feedback.park_id = parks.id 
        ORDER BY feedback.created_at DESC
    """)
    feedbacks = cursor.fetchall()
    
    conn.close()

    parks_html = ""
    for p in parks:
        p_id, p_name, p_loc, p_cuit, p_created, p_paid, p_admin = p
        
        try:
            reg_date = datetime.strptime(p_created.split('.')[0], "%Y-%m-%d %H:%M:%S")
        except:
            reg_date = datetime.now()
            
        days_passed = (datetime.now() - reg_date).days
        days_left_trial = 7 - days_passed
        
        if p_paid == 1:
            status_badge = '<span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold px-3 py-1 rounded-full">🟢 Suscripción Activa (Pago)</span>'
            action_btn = f'<a href="/superadmin/toggle-pay/{p_id}" class="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-3 py-1.5 rounded-xl transition">Pasar a Prueba</a>'
        elif days_left_trial >= 0:
            status_badge = f'<span class="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold px-3 py-1 rounded-full">⏳ En Prueba ({days_left_trial} días restantes)</span>'
            action_btn = f'<a href="/superadmin/toggle-pay/{p_id}" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-xl transition">Forzar Pago Activo</a>'
        else:
            status_badge = '<span class="bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold px-3 py-1 rounded-full">❌ Prueba Expirada</span>'
            action_btn = f'<a href="/superadmin/toggle-pay/{p_id}" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-xl transition">Activar Cuenta</a>'

        parks_html += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-900/60 transition">
            <td class="py-4 px-4 font-black text-white">{p_name}</td>
            <td class="py-4 px-4 text-slate-300 text-xs">{p_loc}</td>
            <td class="py-4 px-4 font-mono text-xs text-emerald-400">{p_cuit}</td>
            <td class="py-4 px-4 font-mono text-xs text-slate-400">{p_admin}</td>
            <td class="py-4 px-4 font-mono text-xs text-slate-400">{p_created} ({days_passed} días atrás)</td>
            <td class="py-4 px-4">{status_badge}</td>
            <td class="py-4 px-4 text-right">{action_btn}</td>
        </tr>
        """

    if not parks_html:
        parks_html = '<tr><td colspan="7" class="py-8 text-center text-slate-500 text-xs italic">No hay parques registrados en la plataforma todavía.</td></tr>'

    feedbacks_html = ""
    for fb in feedbacks:
        msg, fb_date, park_name_fb = fb
        feedbacks_html += f"""
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl">
            <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-black text-emerald-400">🏕️ {park_name_fb}</span>
                <span class="text-[10px] text-slate-500 font-mono">{fb_date}</span>
            </div>
            <p class="text-xs text-slate-300">{msg}</p>
        </div>
        """
    if not feedbacks_html:
        feedbacks_html = '<p class="text-xs text-slate-500 italic">No hay sugerencias enviadas todavía.</p>'

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel SuperAdmin - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 min-h-screen text-slate-100 font-sans p-6 md:p-10">
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-8 bg-slate-900 p-6 rounded-3xl border border-slate-800 shadow-xl">
                <div>
                    <span class="bg-amber-500 text-slate-950 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider">SuperAdmin Central</span>
                    <h1 class="text-2xl md:text-3xl font-black text-white mt-2 tracking-tight">👑 Gestión Global de Parques</h1>
                    <p class="text-xs text-slate-400 mt-0.5">Control total de establecimientos inscriptos, CUITs y estados de suscripción.</p>
                </div>
                <div>
                    <a href="/logout" class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-4 py-3 rounded-xl transition shadow-md">Cerrar Sesión 🚪</a>
                </div>
            </div>

            <!-- Tabla de Parques Registrados -->
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl overflow-x-auto mb-8">
                <h3 class="text-lg font-black text-white mb-4">🌲 Parques Registrados en la Plataforma</h3>
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-[11px] text-slate-400 uppercase font-bold tracking-wider border-b border-slate-800">
                            <th class="pb-3 px-4">Parque</th>
                            <th class="pb-3 px-4">Ubicación</th>
                            <th class="pb-3 px-4">CUIT</th>
                            <th class="pb-3 px-4">Admin</th>
                            <th class="pb-3 px-4">Inscripto</th>
                            <th class="pb-3 px-4">Suscripción</th>
                            <th class="pb-3 px-4 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>{parks_html}</tbody>
                </table>
            </div>

            <!-- Buzón de Sugerencias (Feedback) Abajo -->
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
                <h3 class="text-lg font-black text-white mb-4 flex items-center gap-2">
                    <span>💡</span> Buzón de Sugerencias y Mejoras de los Parques
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {feedbacks_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/superadmin/toggle-pay/<int:park_id>")
def superadmin_toggle_pay(park_id):
    if not session.get("is_super"):
        return redirect(url_for("login"))
        
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_paid FROM parks WHERE id = ?", (park_id,))
    res = cursor.fetchone()
    if res:
        new_paid = 0 if res[0] == 1 else 1
        cursor.execute("UPDATE parks SET is_paid = ? WHERE id = ?", (new_paid, park_id))
        conn.commit()
    conn.close()
    return redirect(url_for("superadmin_panel"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))

    park_id = session["park_id"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        new_capacity = request.form.get("max_capacity")
        new_open = request.form.get("open_time")
        new_close = request.form.get("close_time")

        if new_capacity:
            cursor.execute("UPDATE parks SET max_capacity = ? WHERE id = ?", (new_capacity, park_id))
        if new_open and new_close:
            cursor.execute("UPDATE parks SET open_time = ?, close_time = ? WHERE id = ?", (new_open, new_close, park_id))
        
        conn.commit()
        return redirect(url_for("admin_panel"))

    cursor.execute("SELECT id, name, max_capacity, open_time, close_time, created_at, is_paid FROM parks WHERE id = ?", (park_id,))
    park = cursor.fetchone()

    if not park:
        conn.close()
        return redirect(url_for("logout"))

    park_id, park_name, max_capacity, open_time, close_time, created_at_str, is_paid = park

    try:
        created_at = datetime.strptime(created_at_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
    except:
        created_at = datetime.now() - timedelta(days=1)

    trial_expiration = created_at + timedelta(days=7)
    days_left = (trial_expiration - datetime.now()).days
    is_trial_expired = datetime.now() > trial_expiration and not is_paid

    if is_trial_expired:
        conn.close()
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Suscripción Requerida - TrailControl</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-rose-950 min-h-screen flex items-center justify-center p-6 text-slate-100 selection:bg-rose-500 selection:text-white">
            <div class="bg-slate-900 border border-rose-500/30 p-8 md:p-10 rounded-3xl shadow-2xl max-w-2xl w-full backdrop-blur-md">
                <div class="text-center mb-6">
                    <span class="bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-bold px-3.5 py-1 rounded-full uppercase tracking-wider inline-block mb-2">Prueba Gratuita Finalizada</span>
                    <h1 class="text-2xl md:text-3xl font-black tracking-tight">Elegí tu plan para {park_name}</h1>
                    <p class="text-xs text-slate-300 mt-1">Tus 7 días de prueba han expirado. Seleccioná una opción para mantener tus senderos activos.</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <!-- Plan Mensual -->
                    <div class="bg-slate-950 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between transition hover:border-emerald-500/50">
                        <div>
                            <span class="text-[10px] font-bold uppercase text-slate-400 tracking-wider">Estándar</span>
                            <h3 class="text-base font-black text-white mt-1">Mensual</h3>
                            <div class="my-4">
                                <span class="text-2xl font-black text-emerald-400">$34.000</span>
                                <span class="text-[10px] text-slate-500 block">ARS / mes</span>
                            </div>
                            <p class="text-[11px] text-slate-400">Ideal para evaluar mes a mes sin compromisos.</p>
                        </div>
                        <form action="/crear-suscripcion" method="POST" class="mt-6">
                            <input type="hidden" name="plan" value="mensual">
                            <button type="submit" class="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-2.5 px-3 rounded-xl transition text-xs shadow-md">
                                Seleccionar
                            </button>
                        </form>
                    </div>

                    <!-- Plan Semestral (6x5) -->
                    <div class="bg-slate-950 border border-emerald-500/40 p-5 rounded-2xl flex flex-col justify-between relative shadow-xl shadow-emerald-950/30">
                        <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-600 text-slate-950 font-black text-[9px] uppercase px-3 py-0.5 rounded-full tracking-wider">
                            ¡Ahorras 1 mes! (6x5)
                        </div>
                        <div>
                            <span class="text-[10px] font-bold uppercase text-emerald-400 tracking-wider">Semestral</span>
                            <h3 class="text-base font-black text-white mt-1">6 Meses</h3>
                            <div class="my-4">
                                <span class="text-2xl font-black text-emerald-400">$170.000</span>
                                <span class="text-[10px] text-slate-500 block">Pago único ($28.333/mes)</span>
                            </div>
                            <p class="text-[11px] text-slate-300">Pagás 5 meses y te llevás 6 meses completos.</p>
                        </div>
                        <form action="/crear-suscripcion" method="POST" class="mt-6">
                            <input type="hidden" name="plan" value="semestral">
                            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black py-2.5 px-3 rounded-xl transition text-xs shadow-lg">
                                Elegir Semestral
                            </button>
                        </form>
                    </div>

                    <!-- Plan Anual (12x10) -->
                    <div class="bg-slate-950 border border-emerald-500/60 p-5 rounded-2xl flex flex-col justify-between relative shadow-xl shadow-emerald-950/30">
                        <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-slate-950 font-black text-[9px] uppercase px-3 py-0.5 rounded-full tracking-wider">
                            ¡Ahorras 2 meses! (12x10)
                        </div>
                        <div>
                            <span class="text-[10px] font-bold uppercase text-amber-400 tracking-wider">Anual (Recomendado)</span>
                            <h3 class="text-base font-black text-white mt-1">12 Meses</h3>
                            <div class="my-4">
                                <span class="text-2xl font-black text-emerald-400">$340.000</span>
                                <span class="text-[10px] text-slate-500 block">Pago único ($28.333/mes)</span>
                            </div>
                            <p class="text-[11px] text-slate-300">Pagás 10 meses y te llevás el año entero operativo.</p>
                        </div>
                        <form action="/crear-suscripcion" method="POST" class="mt-6">
                            <input type="hidden" name="plan" value="anual">
                            <button type="submit" class="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-black py-2.5 px-3 rounded-xl transition text-xs shadow-lg">
                                Elegir Anual
                            </button>
                        </form>
                    </div>
                </div>

                <div class="text-center pt-2 border-t border-slate-800">
                    <a href="/logout" class="text-xs font-semibold text-slate-500 hover:text-slate-300 transition">Cerrar Sesión 🚪</a>
                </div>
            </div>
        </body>
        </html>
        """

    park_url = f"http://192.168.0.149:5000/park/{park_id}"
    park_qr_base64 = generate_qr_base64(park_url)
    current_time_str = datetime.now().strftime("%H:%M")

    cursor.execute("""
        SELECT SUM(1 + companions_count) FROM registrations
        JOIN trails ON registrations.trail_id = trails.id
        WHERE trails.park_id = ? AND registrations.status = 'active'
    """, (park_id,))
    active_count_res = cursor.fetchone()[0]
    active_runners = active_count_res if active_count_res else 0

    cursor.execute("SELECT id, name, difficulty, is_open FROM trails WHERE park_id = ?", (park_id,))
    trails = cursor.fetchall()

    trails_admin_html = ""
    for tr in trails:
        tr_id, tr_name, tr_diff, is_open = tr
        status_text = "Abierto (OK)" if is_open else "Cerrado por Clima"
        status_color = "bg-emerald-100 text-emerald-800 border border-emerald-200" if is_open else "bg-rose-100 text-rose-800 border border-rose-200"
        toggle_btn_text = "🔒 Cerrar Sendero" if is_open else "🟢 Abrir Sendero"
        toggle_btn_color = "bg-amber-600 hover:bg-amber-700 shadow-sm" if is_open else "bg-emerald-700 hover:bg-emerald-800 shadow-sm"

        cursor.execute("""
            SELECT runner_name, runner_phone, companions_count, check_in_time, status, sos_active, id, latitude, longitude
            FROM registrations WHERE trail_id = ? ORDER BY check_in_time DESC
        """, (tr_id,))
        registrations = cursor.fetchall()

        regs_html = ""
        if registrations:
            for reg in registrations:
                r_name, r_phone, r_comp, r_time, r_status, r_sos, r_id, r_lat, r_lng = reg
                r_status_badge = '<span class="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-bold">Activo</span>' if r_status == 'active' else '<span class="bg-slate-200 text-slate-700 text-xs px-2.5 py-1 rounded-full">Finalizado</span>'
                
                sos_badge = f'''
                <a href="https://maps.google.com/?q={r_lat},{r_lng}" target="_blank" class="bg-rose-600 hover:bg-rose-700 text-white text-xs px-3 py-1 rounded-full font-black animate-pulse shadow-xs inline-flex items-center gap-1">
                    <span>🚨 ¡SOS ACTIVO!</span> <span class="underline text-[10px]">(Ver Mapa)</span>
                </a>
                ''' if r_sos else ''
                
                inactivity_badge = ' <span class="bg-amber-500 text-slate-950 text-[10px] font-black px-2 py-0.5 rounded-md animate-pulse">⏰ Pasó hora de cierre</span>' if (r_status == 'active' and current_time_str >= close_time) else ''

                regs_html += f"""
                <tr class="border-b border-slate-100 hover:bg-slate-50/80 transition">
                    <td class="py-3.5 px-4 font-bold text-slate-800 flex items-center gap-2 flex-wrap">{r_name} {sos_badge}{inactivity_badge}</td>
                    <td class="py-3.5 px-4 text-slate-600 font-mono text-xs">{r_phone}</td>
                    <td class="py-3.5 px-4 text-slate-600">{r_comp} acompañantes</td>
                    <td class="py-3.5 px-4 text-slate-500 font-mono text-xs">{r_time}</td>
                    <td class="py-3.5 px-4">{r_status_badge}</td>
                </tr>
                """
        else:
            regs_html = '<tr><td colspan="5" class="py-6 text-center text-slate-400 text-xs italic">No hay registros activos en este sendero actualmente.</td></tr>'

        trails_admin_html += f"""
        <div class="bg-white border border-slate-200/90 rounded-3xl p-6 md:p-7 mb-6 shadow-sm">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-5 border-b border-slate-100 pb-4 gap-3">
                <div>
                    <h5 class="font-black text-slate-900 text-lg flex items-center gap-2">
                        🥾 {tr_name} <span class="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">Dificultad: {tr_diff}</span>
                    </h5>
                    <span class="inline-block mt-2 text-xs font-bold px-3 py-1 rounded-full {status_color}">{status_text}</span>
                </div>
                <div>
                    <a href="/admin/toggle-trail/{tr_id}" class="{toggle_btn_color} text-white text-xs font-bold px-4 py-2.5 rounded-xl transition inline-block">
                        {toggle_btn_text}
                    </a>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="text-[11px] text-slate-400 uppercase font-bold tracking-wider border-b border-slate-200">
                            <th class="pb-2.5 px-4">Corredor</th>
                            <th class="pb-2.5 px-4">Teléfono</th>
                            <th class="pb-2.5 px-4">Grupo</th>
                            <th class="pb-2.5 px-4">Check-in</th>
                            <th class="pb-2.5 px-4">Estado</th>
                        </tr>
                    </thead>
                    <tbody>{regs_html}</tbody>
                </table>
            </div>
        </div>
        """

    conn.close()
    capacity_color = "text-emerald-700 bg-emerald-50 border-emerald-200" if active_runners < max_capacity else "text-rose-700 bg-rose-50 border-rose-200 animate-pulse"
    
    days_display = days_left if days_left >= 0 else 0
    trial_banner = f"""
    <div class="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 text-white p-5 rounded-3xl mb-8 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 border border-amber-400/30">
        <div class="flex items-center gap-3">
            <div class="bg-white/20 p-3 rounded-2xl text-2xl shadow-inner">🎁</div>
            <div>
                <span class="text-[10px] font-black uppercase tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">Promoción Lanzamiento</span>
                <h4 class="font-black text-lg mt-1">¡Tenés 7 días de prueba completamente gratis!</h4>
                <p class="text-xs text-amber-100">Disfrutá de todas las funciones B2B sin restricciones en tu establecimiento.</p>
            </div>
        </div>
        <div class="flex items-center gap-4 bg-slate-950/40 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/10">
            <div class="text-center font-mono">
                <span class="text-2xl font-black text-amber-300 block leading-tight">{days_display}</span>
                <span class="text-[10px] uppercase text-slate-300 font-bold">Días Restantes</span>
            </div>
            <div class="h-8 w-[1px] bg-white/20"></div>
            <a href="/crear-suscripcion" class="bg-white hover:bg-slate-100 text-slate-900 text-xs font-black px-4 py-3 rounded-xl transition shadow-md whitespace-nowrap">
                💳 Ver Planes y Pagos
            </a>
        </div>
    </div>
    """ if not is_paid else ''

    feedback_banner = request.args.get("sent")
    feedback_alert = '<div class="bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold p-3.5 rounded-2xl mb-6 shadow-xs">💡 ¡Gracias! Tu sugerencia fue enviada a los desarrolladores de TrailControl con éxito.</div>' if feedback_banner else ''

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Administración - {park_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 min-h-screen text-slate-800 font-sans selection:bg-emerald-500 selection:text-white">
        <div class="max-w-6xl mx-auto py-8 px-6">
            {trial_banner}
            {feedback_alert}
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 bg-white p-6 md:p-8 rounded-3xl shadow-sm border border-slate-200/90 gap-4">
                <div>
                    <span class="bg-emerald-700 text-white text-[10px] font-black px-3.5 py-1 rounded-full uppercase tracking-wider shadow-xs">Panel B2B</span>
                    <h1 class="text-2xl md:text-3xl font-black text-slate-900 mt-2 tracking-tight">🌲 {park_name}</h1>
                    <p class="text-xs text-slate-500 mt-0.5">Monitoreo en tiempo real, aforo en vivo y control de horarios.</p>
                </div>
                <div class="flex items-center gap-3 flex-wrap">
                    <a href="/admin/export-csv" class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-3 rounded-xl transition shadow-md flex items-center gap-2"><span>📊</span> Reporte CSV</a>
                    <a href="/admin/record-trail" class="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold px-4 py-3 rounded-xl transition shadow-md flex items-center gap-2"><span>🛰️</span> Grabar GPS</a>
                    <a href="/" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-3 rounded-xl transition">Ver Sitio</a>
                    <a href="/logout" class="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-4 py-3 rounded-xl transition shadow-md">Salir 🚪</a>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm flex flex-col justify-between">
                    <div>
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Personas Adentro (En Vivo)</span>
                        <div class="flex items-baseline gap-2 mt-2">
                            <span class="text-4xl font-black text-slate-900">{active_runners}</span>
                            <span class="text-sm font-semibold text-slate-500">/ {max_capacity} máx.</span>
                        </div>
                    </div>
                    <div class="mt-4 pt-3 border-t border-slate-100">
                        <span class="text-xs font-bold px-3 py-1 rounded-full border inline-block {capacity_color}">
                            { '⚠️ Capacidad al límite' if active_runners >= max_capacity else '🟢 Aforo Normal' }
                        </span>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm md:col-span-2 flex flex-col justify-between">
                    <div>
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Configuración Operativa ($34.000/mes)</span>
                        <p class="text-xs text-slate-500 mb-4">Modifica el aforo máximo, horarios y mantén al día tu membresía mensual.</p>
                    </div>
                    <form method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                        <div>
                            <label class="block text-[10px] font-bold text-slate-600 uppercase mb-1">Capacidad Máx</label>
                            <input type="number" name="max_capacity" value="{max_capacity}" min="1" max="10000" required class="w-full bg-slate-100 border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-slate-600 uppercase mb-1">Apertura</label>
                            <input type="time" name="open_time" value="{open_time}" required class="w-full bg-slate-100 border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-slate-600 uppercase mb-1">Cierre</label>
                            <input type="time" name="close_time" value="{close_time}" required class="w-full bg-slate-100 border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800">
                        </div>
                        <div class="md:col-span-3 pt-2">
                            <button type="submit" class="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-3 px-4 rounded-xl transition shadow-md">
                                💾 Guardar Cambios
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Buzón de Sugerencias para el Admin del Parque -->
            <div class="bg-white border border-slate-200/90 rounded-3xl p-6 md:p-8 mb-8 shadow-sm">
                <h3 class="text-base font-black text-slate-900 mb-1 flex items-center gap-2">
                    <span>💡</span> Buzón de Sugerencias y Mejoras
                </h3>
                <p class="text-xs text-slate-500 mb-4">¿Te gustaría agregar alguna función nueva o reportar algo? Envianos tu comentario directamente a los desarrolladores.</p>
                <form action="/admin/feedback" method="POST" class="space-y-3">
                    <textarea name="message" rows="2" required placeholder="Ej: Estaría bueno poder agregar un mapa satelital..." class="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-600"></textarea>
                    <button type="submit" class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-5 py-2.5 rounded-xl transition shadow-sm">
                        Enviar Sugerencia 🚀
                    </button>
                </form>
            </div>

            <div class="bg-gradient-to-r from-slate-900 via-emerald-950 to-slate-900 text-white p-8 rounded-3xl mb-8 shadow-xl flex flex-col md:flex-row items-center gap-6 border border-emerald-500/20">
                <div class="bg-white p-3 rounded-2xl shadow-lg">
                    <img src="data:image/png;base64,{park_qr_base64}" alt="QR Parque" class="w-36 h-36 rounded-xl">
                </div>
                <div>
                    <span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-extrabold px-3.5 py-1 rounded-full uppercase tracking-wider">Cartel Principal de Ingreso</span>
                    <h3 class="text-2xl font-black mt-2.5 mb-1 tracking-tight">📱 Código QR Único del Parque</h3>
                    <p class="text-xs text-slate-300 mb-4 max-w-xl leading-relaxed">Imprime este único código QR y colócalo en la entrada principal del complejo para que los visitantes inicien su check-in.</p>
                    <code class="bg-slate-950 text-emerald-400 text-xs font-mono px-3.5 py-2 rounded-xl border border-slate-800 block w-fit shadow-inner">{park_url}</code>
                </div>
            </div>

            <h3 class="text-xl font-black text-slate-900 mb-5">🥾 Listado de Senderos y Monitoreo Activo</h3>
            {trails_admin_html}
        </div>
    </body>
    </html>
    """

@app.route("/crear-suscripcion", methods=["POST", "GET"])
def crear_suscripcion():
    if "admin_id" not in session and request.method == "GET":
        return redirect(url_for("login"))

    park_id = session.get("park_id")
    if not park_id:
        return redirect(url_for("login"))

    if not sdk:
        return "⚠️ La librería 'mercadopago' no está instalada. Ejecute: python -m pip install mercadopago", 500

    plan = request.form.get("plan", "mensual") if request.method == "POST" else "mensual"

    if plan == "semestral":
        title = "TrailControl - Suscripción Semestral (6 Meses - 6x5)"
        amount = 170000.00
    elif plan == "anual":
        title = "TrailControl - Suscripción Anual (12 Meses - 12x10)"
        amount = 340000.00
    else:
        title = "TrailControl - Suscripción Mensual Profesional"
        amount = 34000.00

    success_url = request.host_url + f"pago-exitoso/{park_id}"

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": amount,
                "currency_id": "ARS"
            }
        ],
        "back_urls": {
            "success": success_url,
            "failure": request.host_url + "admin",
            "pending": request.host_url + "admin"
        },
        "auto_return": "approved"
    }

    try:
        result = sdk.preference().create(preference_data)
        if "response" in result and "init_point" in result["response"]:
            payment_url = result["response"]["init_point"]
            return redirect(payment_url)
        else:
            return "⚠️ Error al conectar con Mercado Pago. Verifique sus credenciales de API.", 400
    except Exception as e:
        return f"⚠️️ Error procesando el pago: {str(e)}", 500

@app.route("/pago-exitoso/<int:park_id>")
def pago_exitoso(park_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE parks SET is_paid = 1 WHERE id = ?", (park_id,))
    conn.commit()
    conn.close()

    if "admin_id" in session:
        return redirect(url_for("admin_panel"))
    else:
        return redirect(url_for("login"))

@app.route("/admin/toggle-trail/<int:trail_id>")
def toggle_trail(trail_id):
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_open FROM trails WHERE id = ?", (trail_id,))
    res = cursor.fetchone()
    if res:
        new_status = 0 if res[0] == 1 else 1
        cursor.execute("UPDATE trails SET is_open = ? WHERE id = ?", (new_status, trail_id))
        conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/admin/export-csv")
def export_csv():
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))
    park_id = session["park_id"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trails.name, registrations.runner_name, registrations.runner_phone, 
               registrations.companions_count, registrations.check_in_time, 
               registrations.check_out_time, registrations.status, registrations.sos_active
        FROM registrations JOIN trails ON registrations.trail_id = trails.id WHERE trails.park_id = ?
    """, (park_id,))
    rows = cursor.fetchall()
    conn.close()
    csv_data = "Sendero,Corredor,Telefono,Acompañantes,Check-In,Check-Out,Estado,SOS\n"
    for r in rows:
        csv_data += f'"{r[0]}","{r[1]}","{r[2]}",{r[3]},"{r[4]}","{r[5]}","{r[6]}",{r[7]}\n'
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=reporte_parque.csv"})

@app.route("/admin/record-trail", methods=["GET", "POST"])
def record_trail():
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))
    park_id = session["park_id"]
    if request.method == "POST":
        trail_name = request.form.get("trail_name")
        difficulty = request.form.get("difficulty")
        route_points_json = request.form.get("route_points")
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trails (park_id, name, difficulty, is_open, route_points) VALUES (?, ?, ?, 1, ?)", (park_id, trail_name, difficulty, route_points_json))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_panel"))
    return """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Grabar GPS</title><script src="https://cdn.tailwindcss.com"></script><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" /><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script></head><body class="bg-slate-950 min-h-screen text-slate-100 font-sans p-6"><div class="max-w-3xl mx-auto py-6"><a href="/admin" class="text-xs font-bold text-emerald-400 hover:underline mb-6 inline-block">← Volver</a><div class="bg-slate-900 p-8 rounded-3xl border border-slate-800 shadow-2xl mb-6"><h1 class="text-2xl font-black text-white mb-1">🛰️ Grabador de Sendero GPS</h1><div id="map" class="w-full h-80 rounded-2xl z-10 border border-slate-800 shadow-inner mb-6"></div><div class="flex gap-3 mb-6"><button id="btnStart" onclick="startTracking()" class="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3.5 px-4 rounded-xl">▶️ Iniciar</button><button id="btnStop" onclick="stopTracking()" disabled class="flex-1 bg-rose-600/40 text-white/40 font-bold py-3.5 px-4 rounded-xl cursor-not-allowed">⏹️ Detener</button></div><form method="POST" id="saveForm" class="space-y-4 border-t border-slate-800 pt-6 hidden"><input type="hidden" name="route_points" id="routePointsInput"><div><label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Nombre del Sendero</label><input type="text" name="trail_name" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white"></div><div><label class="block text-xs font-bold text-slate-300 uppercase mb-1.5">Dificultad</label><select name="difficulty" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white"><option value="Fácil">Fácil</option><option value="Moderado">Moderado</option><option value="Difícil">Difícil</option></select></div><button type="submit" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-black py-3.5 px-4 rounded-xl">💾 Guardar Sendero</button></form></div></div><script>let map = L.map('map').setView([-31.4201, -64.4988], 14);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);let watchId = null, latLngs = [];let polyline = L.polyline([], {color: '#10b981', weight: 4}).addTo(map);function startTracking() {latLngs = [];polyline.setLatLngs([]);watchId = navigator.geolocation.watchPosition((pos) => {let lat = pos.coords.latitude, lng = pos.coords.longitude;latLngs.push([lat, lng]);polyline.setLatLngs(latLngs);map.setView([lat, lng], 16);}, null, {enableHighAccuracy: true});document.getElementById('btnStart').disabled = true;document.getElementById('btnStop').disabled = false;}function stopTracking() {if (watchId) navigator.geolocation.clearWatch(watchId);document.getElementById('routePointsInput').value = JSON.stringify(latLngs);document.getElementById('saveForm').classList.remove('hidden');}</script></body></html>"""

@app.route("/park/<int:park_id>")
def park_view(park_id):
    lang = request.args.get("lang", "es")
    if lang not in translations:
        lang = "es"
    t = translations[lang]
    other_lang = "en" if lang == "es" else "es"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, location, open_time, close_time FROM parks WHERE id = ?", (park_id,))
    park = cursor.fetchone()
    if not park:
        conn.close()
        return redirect(url_for('home', lang=lang))
    park_name, park_location, open_time, close_time = park
    cursor.execute("SELECT id, name, difficulty, is_open FROM trails WHERE park_id = ?", (park_id,))
    trails = cursor.fetchall()
    conn.close()
    
    trails_html = ""
    for tr in trails:
        tr_id, tr_name, tr_diff_raw, is_open = tr
        tr_diff = tr_diff_raw if tr_diff_raw else "Moderado"
        
        status_badge = f'''
        <span class="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold px-3 py-1 rounded-full">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> {t["status_open"]}
        </span>
        ''' if is_open else f'''
        <span class="inline-flex items-center gap-1.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-bold px-3 py-1 rounded-full">
            <span class="w-2 h-2 rounded-full bg-rose-500"></span> {t["status_closed"]}
        </span>
        '''
        
        checkin_btn = f'''
        <a href="/checkin/{tr_id}?lang={lang}" class="mt-6 w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black text-base py-4 px-6 rounded-2xl transition flex items-center justify-center gap-3 shadow-lg shadow-emerald-950/50 active:scale-[0.98]">
            <span class="text-xl">⏱️</span> <span>{t["btn_checkin"]}</span>
        </a>
        ''' if is_open else f'''
        <div class="mt-6 w-full bg-slate-900 text-slate-500 font-bold text-sm py-4 px-6 rounded-2xl text-center border border-slate-800 cursor-not-allowed">
            🔒 {t["closed_weather"]}
        </div>
        '''
        
        trails_html += f"""
        <div class="bg-slate-900/90 backdrop-blur-xl p-6 md:p-8 rounded-3xl shadow-2xl border border-slate-800/80 flex flex-col justify-between transition hover:border-emerald-500/40">
            <div>
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
                    <h4 class="font-black text-white text-xl tracking-tight">🥾 {tr_name}</h4>
                    {status_badge}
                </div>
                <div class="flex items-center gap-2 text-sm text-slate-400 mb-2">
                    <span>{t["difficulty"]}:</span>
                    <span class="text-emerald-400 font-extrabold uppercase tracking-wider text-xs bg-emerald-950/60 px-2.5 py-1 rounded-lg border border-emerald-500/20">{tr_diff}</span>
                </div>
            </div>
            {checkin_btn}
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{park_name} - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen text-slate-100 font-sans p-4 sm:p-8 selection:bg-emerald-500 selection:text-white">
        <div class="max-w-3xl mx-auto py-6">
            <div class="flex justify-between items-center mb-6">
                <a href="/?lang={lang}" class="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/20 px-4 py-2.5 rounded-xl hover:bg-emerald-900/40 transition shadow-sm">
                    ← {t["back_home"]}
                </a>
                <a href="/park/{park_id}?lang={other_lang}" class="inline-flex items-center gap-2 text-xs font-bold text-emerald-300 bg-emerald-950/40 border border-emerald-500/20 px-4 py-2.5 rounded-xl hover:bg-emerald-900/60 transition shadow-sm">
                    🌐 {t["lang_switch"]}
                </a>
            </div>
            
            <div class="bg-gradient-to-r from-emerald-900/40 via-slate-900/80 to-slate-900 p-6 sm:p-10 rounded-3xl border border-emerald-500/30 shadow-2xl mb-8 backdrop-blur-xl">
                <span class="bg-emerald-500/20 text-emerald-300 text-[10px] font-black px-3.5 py-1 rounded-full uppercase tracking-wider border border-emerald-500/30 inline-block mb-3">Establecimiento Oficial</span>
                <h1 class="text-3xl sm:text-4xl font-black text-white tracking-tight mb-2">{park_name}</h1>
                <p class="text-emerald-100/80 text-sm sm:text-base flex items-center gap-1.5 mb-4">📍 {park_location}</p>
                <div class="inline-flex items-center gap-2 bg-slate-950/60 border border-slate-800 px-4 py-2 rounded-xl text-xs font-mono text-emerald-300">
                    <span>⏰</span> {t["operating_hours"]}: <strong>{open_time} hs a {close_time} hs</strong>
                </div>
            </div>

            <h3 class="text-xl font-black mb-5 text-white tracking-tight flex items-center gap-2">
                <span>⛰️</span> {t["select_trail"]}
            </h3>
            
            <div class="grid grid-cols-1 gap-5">
                {trails_html}
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/checkin/<int:trail_id>", methods=["GET", "POST"])
def checkin(trail_id):
    lang = request.args.get("lang", "es")
    if lang not in translations:
        lang = "es"
    t = translations[lang]
    other_lang = "en" if lang == "es" else "es"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT trails.name, parks.name, trails.park_id, trails.is_open FROM trails JOIN parks ON trails.park_id = parks.id WHERE trails.id = ?", (trail_id,))
    trail_info = cursor.fetchone()
    conn.close()
    
    if not trail_info or not trail_info[3]:
        return "⚠️ Este sendero se encuentra cerrado.", 403
        
    trail_name, park_name, park_id, is_open = trail_info
    
    if request.method == "POST":
        r_name = request.form.get("runner_name")
        r_phone = request.form.get("runner_phone")
        comps = request.form.get("companions", 0)
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registrations (trail_id, runner_name, runner_phone, companions_count, status, sos_active) VALUES (?, ?, ?, ?, 'active', 0)", (trail_id, r_name, r_phone, comps))
        reg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('active_timer', reg_id=reg_id, lang=lang))
        
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Check-in - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen text-slate-100 flex items-center justify-center p-4 sm:p-6 selection:bg-emerald-500 selection:text-white">
        <div class="bg-slate-900/95 backdrop-blur-2xl p-6 sm:p-10 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl">
            <div class="flex justify-between items-center mb-6">
                <a href="/park/{park_id}?lang={lang}" class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/20 px-3.5 py-2 rounded-xl hover:bg-emerald-900/40 transition">
                    ← {t["back_trail"]}
                </a>
                <a href="/checkin/{trail_id}?lang={other_lang}" class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-300 bg-emerald-950/40 border border-emerald-500/20 px-3.5 py-2 rounded-xl hover:bg-emerald-900/60 transition">
                    🌐 {t["lang_switch"]}
                </a>
            </div>
            
            <div class="mb-6">
                <span class="bg-emerald-500/20 text-emerald-300 text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider border border-emerald-500/30 inline-block mb-2">{t["checkin_subtitle"]}</span>
                <h2 class="text-2xl sm:text-3xl font-black text-white tracking-tight">{t["checkin_title"]}</h2>
                <p class="text-xs sm:text-sm text-slate-400 mt-1">{park_name} • <span class="text-emerald-400 font-bold">{trail_name}</span></p>
            </div>
            
            <form method="POST" class="space-y-5">
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">{t["name_label"]}</label>
                    <input type="text" name="runner_name" required placeholder="Ej: Facundo Gómez" class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3.5 text-sm sm:text-base text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">{t["phone_label"]}</label>
                    <input type="tel" name="runner_phone" required placeholder="Ej: 3541 555555" class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3.5 text-sm sm:text-base text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">{t["companions_label"]}</label>
                    <input type="number" name="companions" value="0" min="0" max="10" class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3.5 text-sm sm:text-base text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition font-bold">
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black text-base py-4 px-6 rounded-2xl transition shadow-lg shadow-emerald-950/50 mt-2 active:scale-[0.98]">
                    🚀 {t["start_button"]}
                </button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/timer/<int:reg_id>")
def active_timer(reg_id):
    lang = request.args.get("lang", "es")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT registrations.runner_name, trails.name, parks.name, registrations.status FROM registrations JOIN trails ON registrations.trail_id = trails.id JOIN parks ON trails.park_id = parks.id WHERE registrations.id = ?", (reg_id,))
    data = cursor.fetchone()
    conn.close()
    
    if not data: 
        return redirect(url_for('home'))
    
    r_name, t_name, p_name, status = data
    
    if status == 'completed':
        return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-slate-950 min-h-screen text-slate-100 flex items-center justify-center p-6"><div class="bg-slate-900 border border-slate-800 p-8 rounded-3xl text-white text-center max-w-md w-full shadow-2xl"><div class="text-5xl mb-3">🎉</div><h2 class="text-2xl font-black mb-2">¡Recorrido Finalizado!</h2><p class="text-xs text-slate-400 mb-6">Tu salida ha sido registrada con éxito en el sistema.</p><a href="/" class="block bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black py-3.5 rounded-2xl">Volver al Inicio</a></div></body></html>"""

    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cronómetro - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            let s = 0;
            setInterval(() => {{
                s++;
                let h = Math.floor(s / 3600);
                let m = Math.floor((s % 3600) / 60);
                let sec = s % 60;
                document.getElementById('timer').innerText = 
                    (h < 10 ? "0" + h : h) + ":" + (m < 10 ? "0" + m : m) + ":" + (sec < 10 ? "0" + sec : sec);
            }}, 1000);

            function triggerSOS() {{
                if (!navigator.geolocation) {{
                    alert("Tu celular no soporta geolocalización para enviar la posición.");
                    window.location.href = "/sos-trigger/{reg_id}?lat=0&lng=0";
                    return;
                }}
                
                document.getElementById('sosBtn').innerText = "🚨 Obteniendo ubicación GPS y enviando alerta...";
                document.getElementById('sosBtn').disabled = true;

                navigator.geolocation.getCurrentPosition(
                    (position) => {{
                        let lat = position.coords.latitude;
                        let lng = position.coords.longitude;
                        window.location.href = `/sos-trigger/{reg_id}?lat=${{lat}}&lng=${{lng}}`;
                    }},
                    (error) => {{
                        alert("No se pudo obtener el GPS exacto, pero enviaremos la alerta de todos modos.");
                        window.location.href = "/sos-trigger/{reg_id}?lat=0&lng=0";
                    }},
                    {{ enableHighAccuracy: true, timeout: 10000 }}
                );
            }}
        </script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 min-h-screen text-slate-100 flex items-center justify-center p-4 sm:p-6 selection:bg-emerald-500 selection:text-white">
        <div class="bg-slate-900/95 backdrop-blur-2xl p-6 sm:p-8 rounded-3xl max-w-md w-full text-center shadow-2xl border border-slate-800">
            <div class="bg-emerald-500/20 text-emerald-300 text-xs font-bold px-3.5 py-1 rounded-full mb-4 inline-block border border-emerald-500/30">🟢 Recorrido en Curso</div>
            <h2 class="text-2xl font-black text-white tracking-tight">{r_name}</h2>
            <p class="text-xs text-slate-400 mb-6">{p_name} • <span class="font-bold text-emerald-400">{t_name}</span></p>
            <div id="timer" class="bg-slate-950 text-emerald-400 font-mono text-5xl sm:text-6xl font-extrabold py-8 rounded-2xl mb-6 shadow-inner tracking-wider border border-slate-800/80">00:00:00</div>
            <a href="/checkout/{reg_id}" class="block bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-black py-4 px-6 rounded-2xl transition shadow-lg shadow-emerald-950/50 mb-3 text-base">🏁 FINALIZAR (CHECK-OUT)</a>
            <button id="sosBtn" onclick="triggerSOS()" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-black py-4 px-6 rounded-2xl transition shadow-lg shadow-rose-950/50 cursor-pointer text-base">🚨 BOTÓN DE EMERGENCIA (SOS)</button>
        </div>
    </body>
    </html>
    """

@app.route("/sos-trigger/<int:reg_id>")
def sos_trigger(reg_id):
    lat = request.args.get("lat", "0")
    lng = request.args.get("lng", "0")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET sos_active = 1, latitude = ?, longitude = ? WHERE id = ?", (lat, lng, reg_id))
    conn.commit()
    conn.close()
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOS Enviado - TrailControl</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-950 via-rose-950 to-slate-950 min-h-screen text-white flex items-center justify-center p-4 sm:p-6">
        <div class="bg-slate-900/95 border border-rose-500/40 p-6 sm:p-8 rounded-3xl max-w-md w-full text-center shadow-2xl backdrop-blur-xl">
            <div class="text-5xl mb-3 animate-bounce">🚨</div>
            <h2 class="text-2xl font-black mb-2 text-rose-400 tracking-tight">¡Alerta SOS Transmitida!</h2>
            <p class="text-xs sm:text-sm text-slate-300 mb-6 leading-relaxed">
                Los guardaparques y administradores han recibido tu pedido de auxilio junto con tu posición GPS exacta. Mantén la calma y quédate en un lugar seguro.
            </p>
            <div class="bg-slate-950 p-3.5 rounded-2xl border border-slate-800 text-xs font-mono text-slate-400 mb-6 shadow-inner">
                Lat: {lat} | Lng: {lng}
            </div>
            <a href="https://maps.google.com/?q={lat},{lng}" target="_blank" class="block bg-blue-600 hover:bg-blue-500 text-white font-black py-3.5 rounded-2xl mb-3 text-xs transition shadow-lg">
                🗺️ Ver mi ubicación en Google Maps
            </a>
            <a href="/timer/{reg_id}" class="text-xs font-bold text-slate-400 hover:text-white transition underline">Volver al cronómetro</a>
        </div>
    </body>
    </html>
    """

@app.route("/checkout/<int:reg_id>")
def checkout(reg_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET status = 'completed', check_out_time = CURRENT_TIMESTAMP WHERE id = ?", (reg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('active_timer', reg_id=reg_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)