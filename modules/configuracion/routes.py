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

    return render_template("configuracion.html", index=index)


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
        flash("⚠️ No se puede quitar el permiso de administrador al usuario principal.", "error")
        return redirect(url_for("configuracion.permisos"))

    if usuario_id == session["id_usuario"] and admin_sistema_valor == 0:
        conn.close()
        flash("⚠️ No puedes quitarte tu propio permiso de administrador.", "error")
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
