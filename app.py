from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import os
import io
import qrcode
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_super_segura_trail_control")

DB_NAME = "database.db"

try:
    import mercadopago
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "TEST-tu-access-token-de-mercado-pago-aqui")
    sdk = mercadopago.SDK(mp_token)
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
        "disclaimer_text": "TrailControl es una herramienta tecnológica de software orientada a facilitar la gestión de aforos, el registro de ingresos y el monitoreo de senderos. La plataforma no sustituye los servicios de rescate profesionales, la señalización física en terreno, ni la responsabilidad individual de los visitantes sobre su propia seguridad y estado físico.",
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
        "disclaimer_text": "TrailControl is a software technology tool designed to facilitate capacity management, visitor registration, and trail monitoring.",
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
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if os.path.exists("schema.sql"):
            with open("schema.sql", "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
        cursor.execute("""
            INSERT OR IGNORE INTO admins (id, username, password, park_id, is_super) 
            VALUES (999, 'facu_master', 'trail2026', NULL, 1)
        """)
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
    return render_template("index.html", t=t, lang=lang, other_lang=other_lang)

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
        username = request.form.get("username")
        password = request.form.get("password")

        if not terms:
            error = "⚠️ Debes aceptar los Términos y Condiciones para continuar."
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO parks (name, location, cuit, latitude, longitude, max_capacity, is_paid)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (park_name, location, cuit, latitude, longitude, max_capacity))
                park_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO admins (username, password, park_id, is_super)
                    VALUES (?, ?, ?, 0)
                """, (username, password, park_id))

                conn.commit()
                conn.close()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                conn.close()
                error = "El CUIT ya está registrado o el nombre de usuario de administrador ya existe."

    return render_template("register_park.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect(DB_NAME)
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

    return render_template("login.html", error=error)

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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (park_id, message) VALUES (?, ?)", (park_id, message))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_panel") + "?sent=true")

@app.route("/superadmin")
def superadmin_panel():
    if not session.get("is_super"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT parks.id, parks.name, parks.location, parks.cuit, parks.created_at, parks.is_paid, admins.username
        FROM parks LEFT JOIN admins ON parks.id = admins.park_id WHERE admins.is_super = 0
    """)
    parks = cursor.fetchall()
    cursor.execute("""
        SELECT feedback.message, feedback.created_at, parks.name 
        FROM feedback JOIN parks ON feedback.park_id = parks.id 
        ORDER BY feedback.created_at DESC
    """)
    feedbacks = cursor.fetchall()
    conn.close()
    return render_template("superadmin.html", parks=parks, feedbacks=feedbacks)

@app.route("/superadmin/toggle-pay/<int:park_id>")
def superadmin_toggle_pay(park_id):
    if not session.get("is_super"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
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
        return render_template("subscription_required.html", park_name=park_name)

    park_url = request.host_url.rstrip('/') + f"/park/{park_id}"
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

    trails_data = []
    for tr in trails:
        tr_id, tr_name, tr_diff, is_open = tr
        cursor.execute("""
            SELECT runner_name, runner_phone, companions_count, check_in_time, status, sos_active, id, latitude, longitude
            FROM registrations WHERE trail_id = ? ORDER BY check_in_time DESC
        """, (tr_id,))
        regs = cursor.fetchall()
        trails_data.append({
            "id": tr_id, "name": tr_name, "difficulty": tr_diff, "is_open": is_open, "registrations": regs
        })

    conn.close()
    days_display = days_left if days_left >= 0 else 0
    feedback_banner = request.args.get("sent")

    return render_template("admin.html",
                           park_name=park_name, max_capacity=max_capacity, open_time=open_time,
                           close_time=close_time, active_runners=active_runners, days_left=days_display,
                           is_paid=is_paid, park_url=park_url, park_qr_base64=park_qr_base64,
                           trails=trails_data, current_time_str=current_time_str, feedback_sent=feedback_banner)

@app.route("/crear-suscripcion", methods=["POST", "GET"])
def crear_suscripcion():
    if "admin_id" not in session and request.method == "GET":
        return redirect(url_for("login"))
    park_id = session.get("park_id")
    if not park_id or not sdk:
        return "⚠️ Mercado Pago no configurado o sesión inválida.", 400

    plan = request.form.get("plan", "mensual") if request.method == "POST" else "mensual"
    if plan == "semestral":
        title, amount = "TrailControl - Semestral (6x5)", 170000.00
    elif plan == "anual":
        title, amount = "TrailControl - Anual (12x10)", 340000.00
    else:
        title, amount = "TrailControl - Mensual", 34000.00

    success_url = request.host_url.rstrip('/') + f"/pago-exitoso/{park_id}"
    preference_data = {
        "items": [{"title": title, "quantity": 1, "unit_price": amount, "currency_id": "ARS"}],
        "back_urls": {"success": success_url, "failure": request.host_url.rstrip('/') + "/admin", "pending": request.host_url.rstrip('/') + "/admin"},
        "auto_return": "approved"
    }
    try:
        result = sdk.preference().create(preference_data)
        if "response" in result and "init_point" in result["response"]:
            return redirect(result["response"]["init_point"])
    except Exception as e:
        return f"Error: {str(e)}", 500
    return "Error al conectar con Mercado Pago", 400

@app.route("/pago-exitoso/<int:park_id>")
def pago_exitoso(park_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE parks SET is_paid = 1 WHERE id = ?", (park_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel") if "admin_id" in session else url_for("login"))

@app.route("/admin/toggle-trail/<int:trail_id>")
def toggle_trail(trail_id):
    if "admin_id" not in session or session.get("is_super"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trails (park_id, name, difficulty, is_open, route_points) VALUES (?, ?, ?, 1, ?)", (park_id, trail_name, difficulty, route_points_json))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_panel"))
    return render_template("record_trail.html")

@app.route("/park/<int:park_id>")
def park_view(park_id):
    lang = request.args.get("lang", "es")
    if lang not in translations:
        lang = "es"
    t = translations[lang]
    other_lang = "en" if lang == "es" else "es"

    conn = sqlite3.connect(DB_NAME)
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
    return render_template("park_view.html", park_name=park_name, park_location=park_location, open_time=open_time, close_time=close_time, trails=trails, park_id=park_id, t=t, lang=lang, other_lang=other_lang)

@app.route("/checkin/<int:trail_id>", methods=["GET", "POST"])
def checkin(trail_id):
    lang = request.args.get("lang", "es")
    if lang not in translations:
        lang = "es"
    t = translations[lang]
    other_lang = "en" if lang == "es" else "es"

    conn = sqlite3.connect(DB_NAME)
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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registrations (trail_id, runner_name, runner_phone, companions_count, status, sos_active) VALUES (?, ?, ?, ?, 'active', 0)", (trail_id, r_name, r_phone, comps))
        reg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('active_timer', reg_id=reg_id, lang=lang))

    return render_template("checkin.html", trail_name=trail_name, park_name=park_name, park_id=park_id, trail_id=trail_id, t=t, lang=lang, other_lang=other_lang)

@app.route("/timer/<int:reg_id>")
def active_timer(reg_id):
    lang = request.args.get("lang", "es")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT registrations.runner_name, trails.name, parks.name, registrations.status FROM registrations JOIN trails ON registrations.trail_id = trails.id JOIN parks ON trails.park_id = parks.id WHERE registrations.id = ?", (reg_id,))
    data = cursor.fetchone()
    conn.close()
    if not data:
        return redirect(url_for('home'))
    r_name, t_name, p_name, status = data
    if status == 'completed':
        return render_template("completed.html", lang=lang)
    return render_template("timer.html", reg_id=reg_id, r_name=r_name, t_name=t_name, p_name=p_name, lang=lang)

@app.route("/sos-trigger/<int:reg_id>")
def sos_trigger(reg_id):
    lat = request.args.get("lat", "0")
    lng = request.args.get("lng", "0")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET sos_active = 1, latitude = ?, longitude = ? WHERE id = ?", (lat, lng, reg_id))
    conn.commit()
    conn.close()
    return render_template("sos_triggered.html", lat=lat, lng=lng, reg_id=reg_id)

@app.route("/checkout/<int:reg_id>")
def checkout(reg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE registrations SET status = 'completed', check_out_time = CURRENT_TIMESTAMP WHERE id = ?", (reg_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('active_timer', reg_id=reg_id))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)