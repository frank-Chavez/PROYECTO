from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
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
from werkzeug.security import check_password_hash


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "clave_temporal"

# -------------------- Configuración de Correo --------------------
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", app.config["MAIL_USERNAME"])

mail = Mail(app)


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

    error = None

    if request.method == "POST":
        usuario = request.form.get("username")
        password = request.form.get("password")

        conn = conection()
        cursor = conn.cursor()

        # Buscar usuario
        cursor.execute("SELECT * FROM Usuario WHERE nombre_u = ?", (usuario,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            # --- INICIO DE SESIÓN EXITOSO ---
            session["id_usuario"] = user["id_usuario"]
            session["nombre_u"] = user["nombre_u"]
            session["rol_id"] = user["rol_id"]

            # Nombre del rol
            cursor.execute("SELECT tipo_rol FROM Rol WHERE rol_id = ?", (user["rol_id"],))
            rol = cursor.fetchone()
            session["rol_nombre"] = rol["tipo_rol"] if rol else "Desconocido"

            # ========= CARGAR PERMISOS POR MÓDULO (NUEVO SISTEMA) =========
            cursor.execute(
                """
                SELECT m.clave_modulo, pm.ver, pm.crear, pm.editar, pm.eliminar, pm.exportar
                FROM PermisoModulo pm
                JOIN Modulo m ON pm.modulo_id = m.id_modulo
                WHERE pm.usuario_id = ?
            """,
                (user["id_usuario"],),
            )
            permisos_raw = cursor.fetchall()

            permisos_dict = {"administrar_sistema": False}

            for fila in permisos_raw:
                clave = fila["clave_modulo"]
                permisos_dict[clave] = {
                    "ver": bool(fila["ver"]),
                    "crear": bool(fila["crear"]),
                    "editar": bool(fila["editar"]),
                    "eliminar": bool(fila["eliminar"]),
                    "exportar": bool(fila["exportar"]),
                }
            # ¡¡AQUÍ ESTÁ EL CAMBIO CLAVE!!
            # Solo el ROL 1 o el usuario ID=1 son administradores del sistema
            if user["rol_id"] == 1 or user["id_usuario"] == 1:
                permisos_dict["administrar_sistema"] = True
            else:
                permisos_dict["administrar_sistema"] = False

            # Superadmin (id=1) tiene TODO aunque no esté en la BD
            if user["id_usuario"] == 1:
                claves = [
                    "cotizaciones",
                    "planes",
                    "servicios",
                    "proveedores",
                    "familiares",
                    "fallecidos",
                    "configuracion",
                    "reportes",
                ]
                for clave in claves:
                    permisos_dict[clave] = {
                        "ver": True,
                        "crear": True,
                        "editar": True,
                        "eliminar": True,
                        "exportar": True,
                    }
            session["permisos"] = permisos_dict

            conn.close()
            flash(f"Bienvenido, {user['nombre_u']}!", "success")
            return redirect(url_for("dashboar"))

        # Si falla
        error = "Usuario o contraseña incorrectos"
        if user:
            conn.close()

    return render_template("login.html", error=error)


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
