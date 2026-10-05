import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "trailcontrol_secret_key_super_segura"

DATABASE = "database.db"


def get_db_connection():
  conn = sqlite3.connect(DATABASE)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  """Crea las tablas automáticamente si no existen al iniciar la app"""
  conn = get_db_connection()
  conn.execute("""
        CREATE TABLE IF NOT EXISTS parks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            admin_user TEXT NOT NULL,
            admin_pass TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            park_id INTEGER,
            message TEXT NOT NULL,
            lat TEXT,
            lon TEXT,
            status TEXT DEFAULT 'Pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (park_id) REFERENCES parks (id)
        )
    """)
  conn.commit()
  conn.close()


@app.route("/")
def index():
  return render_template("index.html")


# ─── REGISTRO DE PARQUES (Público / Directo) ──────────────────────────
@app.route("/register-park", methods=["GET", "POST"])
def register_park():
  if request.method == "POST":
    name = request.form.get("name")
    code = request.form.get("code")
    admin_user = request.form.get("admin_user")
    admin_pass = request.form.get("admin_pass")

    try:
      conn = get_db_connection()
      conn.execute(
          "INSERT INTO parks (name, code, admin_user, admin_pass) VALUES (?, ?,"
          " ?, ?)",
          (name, code, admin_user, admin_pass),
      )
      conn.commit()
      conn.close()
      flash("¡Parque registrado exitosamente!", "success")
      return redirect(url_for("index"))
    except Exception as e:
      flash(f"Error al registrar el parque (código repetido o inválido): {e}", "danger")

  return render_template("register_park.html")


# ─── SUPER ADMIN PANEL (facu_master / trail2026) ─────────────────────
@app.route("/superadmin", methods=["GET", "POST"])
def superadmin():
  if request.method == "POST":
    user = request.form.get("username")
    pwd = request.form.get("password")
    if user == "facu_master" and pwd == "trail2026":
      session["superadmin"] = True
      return redirect(url_for("superadmin_dashboard"))
    else:
      flash("Credenciales de SuperAdmin incorrectas", "danger")
  return render_template("superadmin_login.html")


@app.route("/superadmin/dashboard")
def superadmin_dashboard():
  if not session.get("superadmin"):
    return redirect(url_for("superadmin"))
  conn = get_db_connection()
  parks = conn.execute("SELECT * FROM parks").fetchall()
  conn.close()
  return render_template("superadmin_dashboard.html", parks=parks)


@app.route("/superadmin/park/create", methods=["POST"])
def create_park():
  if not session.get("superadmin"):
    return redirect(url_for("superadmin"))

  name = request.form.get("name")
  code = request.form.get("code")
  admin_user = request.form.get("admin_user")
  admin_pass = request.form.get("admin_pass")

  try:
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO parks (name, code, admin_user, admin_pass) VALUES (?, ?,"
        " ?, ?)",
        (name, code, admin_user, admin_pass),
    )
    conn.commit()
    conn.close()
    flash("Parque creado exitosamente", "success")
  except Exception as e:
    flash(f"Error al crear el parque: {e}", "danger")

  return redirect(url_for("superadmin_dashboard"))


@app.route("/superadmin/logout")
def superadmin_logout():
  session.pop("superadmin", None)
  return redirect(url_for("superadmin"))


# Inicializar base de datos al arrancar
init_db()

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)