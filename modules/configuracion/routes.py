from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from database import conection


configuracion_bd = Blueprint(
    "configuracion", __name__, url_prefix="/configuracion", template_folder="templates", static_folder="static"
)


@configuracion_bd.route("/usuarios")
def index():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if not session.get("permisos", {}).get("administrar_sistema"):
        flash("No tienes permiso para acceder a esta sección.")
        return redirect(url_for("dashboar"))
    conn = conection()
    index = conn.execute(
        """
        SELECT u.*, 
               IFNULL(SUM(
                   p.ver_registros + 
                   p.crear_registros + 
                   p.editar_registros + 
                   p.eliminar_registros + 
                   p.exportar_datos + 
                   p.administrar_sistema
               ), 0) AS total_permisos
        FROM Usuario u
        LEFT JOIN PermisosUsuario p ON u.id_usuario = p.usuario_id
        GROUP BY u.id_usuario
    """
    ).fetchall()
    conn.close()

    return render_template("configuracion.html", index=index, title="Usuarios")


# --- proteccion para todas las rutas del modulo de configuracion solo el admin o el que tenga permiso puede entrar al modulo
@configuracion_bd.before_request
def verificar_permisos_config():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if not session.get("permisos", {}).get("administrar_sistema"):
        flash("No tienes permiso para acceder a la configuración.", "danger")
        return redirect(url_for("dashboar"))


@configuracion_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        configuracion = conn.execute(
            """SELECT * FROM Usuario 
            WHERE LOWER(remove_acentos(nombre_u)) LIKE ?""",
            ("%" + search + "%",),
        ).fetchall()
        conn.close()
        return render_template("configuracion.html", index=configuracion, busqueda=search, title="Usuarios")
    return redirect(url_for("configuracion.index"))


@configuracion_bd.route("/permisos")
def permisos():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id_usuario, u.nombre_u, u.rol_id,
                   IFNULL(p.ver_registros, 0) AS ver_registros,
                   IFNULL(p.crear_registros, 0) AS crear_registros,
                   IFNULL(p.editar_registros, 0) AS editar_registros,
                   IFNULL(p.eliminar_registros, 0) AS eliminar_registros,
                   IFNULL(p.exportar_datos, 0) AS exportar_datos,
                   IFNULL(p.administrar_sistema, 0) AS administrar_sistema
            FROM Usuario u
                   LEFT JOIN PermisosUsuario p ON u.id_usuario = p.usuario_id
                   """
    )
    permisos = cursor.fetchall()
    conn.close()

    return render_template("permisos.html", permisos=permisos, title="Permisos")


@configuracion_bd.route("/guardar_permisos", methods=["POST"])
def guardar_permisos():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cursor = conn.cursor()

    usuario_id = int(request.form.get("usuario_id"))

    # Tomamos el valor enviado
    admin_sistema_valor = 1 if "administrar_sistema" in request.form else 0

    # Validaciones de seguridad
    if usuario_id == 1 and admin_sistema_valor == 0:
        conn.close()
        flash("No se puede quitar el permiso de administrador al usuario principal.", "error")
        return redirect(url_for("configuracion.permisos"))

    if usuario_id == session["id_usuario"] and admin_sistema_valor == 0:
        conn.close()
        flash("No puedes quitarte tu propio permiso de administrador.", "error")
        return redirect(url_for("configuracion.permisos"))

    # Construimos permisos con validaciones aplicadas
    permisos = {
        "ver_registros": 1 if "ver_registros" in request.form else 0,
        "crear_registros": 1 if "crear_registros" in request.form else 0,
        "editar_registros": 1 if "editar_registros" in request.form else 0,
        "eliminar_registros": 1 if "eliminar_registros" in request.form else 0,
        "exportar_datos": 1 if "exportar_datos" in request.form else 0,
        "administrar_sistema": admin_sistema_valor,  # ya validado
    }

    # Verificar si ya tiene registro en PermisosUsuario
    cursor.execute("SELECT * FROM PermisosUsuario WHERE usuario_id = ?", (usuario_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE PermisosUsuario
            SET ver_registros = ?, crear_registros = ?, editar_registros = ?, 
                eliminar_registros = ?, exportar_datos = ?, administrar_sistema = ?
            WHERE usuario_id = ?
            """,
            (
                permisos["ver_registros"],
                permisos["crear_registros"],
                permisos["editar_registros"],
                permisos["eliminar_registros"],
                permisos["exportar_datos"],
                permisos["administrar_sistema"],
                usuario_id,
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO PermisosUsuario (
                usuario_id, ver_registros, crear_registros, editar_registros,
                eliminar_registros, exportar_datos, administrar_sistema
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                usuario_id,
                permisos["ver_registros"],
                permisos["crear_registros"],
                permisos["editar_registros"],
                permisos["eliminar_registros"],
                permisos["exportar_datos"],
                permisos["administrar_sistema"],
            ),
        )

    # Si el usuario editado es el que está logueado, actualizar sesión
    if usuario_id == session["id_usuario"]:
        session["permisos"] = permisos

    conn.commit()
    conn.close()

    flash("Permisos actualizados correctamente.")
    return redirect(url_for("configuracion.permisos") + f"#usuario-{usuario_id}")


@configuracion_bd.route("/agregar_usuario", methods=["GET", "POST"])
def agregar_usuario():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        rol = request.form["rol"]

        conn = conection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Usuario (nombre_u, contraseña_u, rol_id)
            VALUES (?, ?, ?)
        """,
            (nombre, contraseña, rol),
        )
        usuario_id = cursor.lastrowid

        if rol == "1":
            permisos = (1, 1, 1, 1, 1, 1)
        else:
            permisos = (1, 1, 1, 0, 0, 0)
        cursor.execute(
            """
                INSERT INTO PermisosUsuario (
                    usuario_id, ver_registros, crear_registros, editar_registros,
                    eliminar_registros, exportar_datos, administrar_sistema
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (usuario_id, *permisos),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("configuracion.agregar_usuario"))

    return render_template("AgregarUsuario.html", title="Agregar Usuario")


@configuracion_bd.route("/eliminar_usuario/<int:usuario_id>", methods=["POST"])
def eliminar_usuario(usuario_id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if usuario_id == 1:
        flash("No se puede eliminar el usuario principal.", "error")
        return redirect(url_for("configuracion.index"))

    if usuario_id == session["id_usuario"]:
        flash("No puedes eliminar tu propio usuario.", "error")
        return redirect(url_for("configuracion.index"))

    conn = conection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM PermisosUsuario WHERE usuario_id = ?", (usuario_id,))
    cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?", (usuario_id,))

    conn.commit()
    conn.close()

    flash("Usuario eliminado correctamente.")
    return redirect(url_for("configuracion.index"))


@configuracion_bd.route("/seguridad")
def seguridad():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Usuario ")
    usuarios = cursor.fetchall()
    conn.close()

    return render_template("seguridad.html", seguridad=usuarios, title="Seguridad")
