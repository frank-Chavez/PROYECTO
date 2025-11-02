from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import conection
from dotenv import load_dotenv
import os
from modules.familiares.routes import familiares_bd
from modules.fallecidos.routes import fallecidos_bd
from modules.plan.routes import planes_bd
from modules.proveedores.routes import proveedor_bd
from modules.servicios.routes import servicios_bd
from modules.cotizaciones.routes import cotizaciones_bd
from modules.configuracion.routes import configuracion_bd

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "clave_temporal"


# -------------------- Evitar cache --------------------
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


# -------------------- Blueprints --------------------
app.register_blueprint(familiares_bd)
app.register_blueprint(fallecidos_bd)
app.register_blueprint(planes_bd)
app.register_blueprint(proveedor_bd)
app.register_blueprint(servicios_bd)
app.register_blueprint(cotizaciones_bd)
app.register_blueprint(configuracion_bd)


# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if "id_usuario" in session:
        return redirect(url_for("dashboar"))

    mensaje = None
    if request.method == "POST":
        usuario = request.form.get("username")
        password = request.form.get("password")

        conn = conection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Usuario WHERE nombre_u=? AND contraseña_u=?", (usuario, password))
        user = cursor.fetchone()

        if user:
            session["id_usuario"] = user["id_usuario"]
            session["nombre_u"] = user["nombre_u"]
            session["rol_id"] = user["rol_id"]

            # Nombre del rol
            cursor.execute("SELECT tipo_rol FROM Rol WHERE rol_id=?", (user["rol_id"],))
            rol = cursor.fetchone()
            session["rol_nombre"] = rol["tipo_rol"] if rol else "Desconocido"

            # Permisos
            cursor.execute("SELECT * FROM PermisosUsuario WHERE usuario_id=?", (user["id_usuario"],))
            permisos = cursor.fetchone()
            session["permisos"] = dict(permisos) if permisos else {}

            conn.close()
            return redirect(url_for("dashboar"))

        mensaje = "Usuario o contraseña incorrectos"
        conn.close()

    return render_template("login.html", mensaje=mensaje)


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------- DASHBOARD --------------------
@app.route("/dashboar", endpoint="dashboar")
def dashboar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    def count_safe(query):
        r = conn.execute(query).fetchone()
        return r["n"] if r else 0

    familiares_count = count_safe(
        "SELECT COUNT(*) AS n FROM Familiares WHERE LOWER(TRIM(f_estado))='activo' OR TRIM(f_estado)='1'"
    )
    servicios_count = count_safe(
        "SELECT COUNT(*) AS n FROM Servicios WHERE LOWER(TRIM(estado_serv))='activo' OR TRIM(estado_serv)='1'"
    )
    cotizaciones_count = count_safe(
        "SELECT COUNT(*) AS n FROM Cotizacion WHERE LOWER(TRIM(fecha_cot))='activo' OR TRIM(estado_cot)='1'"
    )
    proveedores_count = count_safe(
        "SELECT COUNT(*) AS n FROM Proveedores WHERE LOWER(TRIM(estado_p))='activo' OR TRIM(estado_p)='1'"
    )

    # Últimos registros
    reciente_familiar = conn.execute(
        "SELECT (COALESCE(f_nombre,'') || ' ' || COALESCE(f_apellido,'')) AS nombre, fechaRegistro "
        "FROM Familiares ORDER BY (fechaRegistro IS NULL), datetime(fechaRegistro) DESC, id_familiar DESC LIMIT 1"
    ).fetchone()

    reciente_cotizacion = conn.execute(
        "SELECT numero_cot, fecha_cot FROM Cotizacion ORDER BY datetime(fecha_cot) DESC, id_cotizacion DESC LIMIT 1"
    ).fetchone()

    reciente_servicio = conn.execute(
        "SELECT tipo_serv, estado_serv FROM Servicios ORDER BY id_servicio DESC LIMIT 1"
    ).fetchone()

    reciente_proveedor = conn.execute(
        "SELECT nombre_p, fechaRegistro_p FROM Proveedores ORDER BY datetime(fechaRegistro_p) DESC, id_proveedor DESC LIMIT 1"
    ).fetchone()

    conn.close()

    return render_template(
        "dashboar.html",
        familiares_count=familiares_count,
        servicios_count=servicios_count,
        cotizaciones_count=cotizaciones_count,
        proveedores_count=proveedores_count,
        reciente_familiar=reciente_familiar,
        reciente_cotizacion=reciente_cotizacion,
        reciente_servicio=reciente_servicio,
        reciente_proveedor=reciente_proveedor,
        title="Dashboard",
        # Esto asegura que en la plantilla siempre exista permisos
        permisos=session.get("permisos", {}),
    )


if __name__ == "__main__":
    app.run(debug=True)
