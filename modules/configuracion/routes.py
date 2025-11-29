from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from database import conection
from werkzeug.security import generate_password_hash

configuracion_bd = Blueprint(
    "configuracion", __name__, url_prefix="/configuracion", template_folder="templates", static_folder="static"
)

# ---------------------------------------------------------------------------
# Usuarios (list)
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
        SELECT 
            u.id_usuario,
            u.nombre_u,
            u.rol_id,
            COALESCE(SUM(CASE WHEN pm.modulo_id != 7 THEN pm.ver + pm.crear + pm.editar + pm.eliminar + pm.exportar ELSE 0 END), 0)
            + MAX(CASE WHEN pm.modulo_id = 7 AND (pm.ver+pm.crear+pm.editar+pm.eliminar+pm.exportar) > 0 THEN 1 ELSE 0 END) AS total_permisos
        FROM Usuario u
        LEFT JOIN PermisoModulo pm ON u.id_usuario = pm.usuario_id
        GROUP BY u.id_usuario
        ORDER BY u.nombre_u
        """
    ).fetchall()
    conn.close()
    return render_template("configuracion.html", index=index, title="Usuarios")

# ---------------------------------------------------------------------------
# Protección global del módulo
@configuracion_bd.before_request
def verificar_permisos_config():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if not session.get("permisos", {}).get("administrar_sistema"):
        flash("No tienes permiso para acceder a la configuración.", "danger")
        return redirect(url_for("dashboar"))

# ---------------------------------------------------------------------------
# Buscador
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



# ---------------------------------------------------------------------------
# Cargar permisos en sesión (helper)
def cargar_permisos_en_sesion(usuario_id):
    conn = conection()
    permisos = conn.execute(
        """
        SELECT m.clave_modulo, pm.ver, pm.crear, pm.editar, pm.eliminar, pm.exportar
        FROM PermisoModulo pm
        JOIN Modulo m ON pm.modulo_id = m.id_modulo
        WHERE pm.usuario_id = ?
        """,
        (usuario_id,),
    ).fetchall()
    conn.close()
    permisos_dict = {"administrar_sistema": False}
    for p in permisos:
        clave = p[0]
        permisos_dict[clave] = {"ver": bool(p[1]), "crear": bool(p[2]), "editar": bool(p[3]), "eliminar": bool(p[4]), "exportar": bool(p[5])}
    session["permisos"] = permisos_dict

# ---------------------------------------------------------------------------
# Guardar permisos (used by both permisos page and edit page)
@configuracion_bd.route("/guardar_permisos_modulo", methods=["POST"])
def guardar_permisos_modulo():
    if "id_usuario" not in session or not session["permisos"].get("administrar_sistema"):
        return redirect(url_for("login"))

    usuario_id = int(request.form["usuario_id"])
    if usuario_id == 1:
        flash("No puedes modificar los permisos del administrador principal.", "error")
        return redirect(url_for("configuracion.editar_usuario", usuario_id=usuario_id))

    conn = conection()
    cursor = conn.cursor()
    ID_MODULO_CONFIGURACION = 7
    modulos = cursor.execute("SELECT id_modulo, clave_modulo FROM Modulo").fetchall()
    for modulo in modulos:
        modulo_id = modulo[0]
        if modulo_id == ID_MODULO_CONFIGURACION:
            tiene_acceso = request.form.get("acceso_configuracion") == "1"
            ver = crear = editar = eliminar = exportar = 1 if tiene_acceso else 0
        else:
            prefix = f"modulo_{modulo_id}"
            ver = 1 if request.form.get(f"{prefix}_ver") else 0
            crear = 1 if request.form.get(f"{prefix}_crear") else 0
            editar = 1 if request.form.get(f"{prefix}_editar") else 0
            eliminar = 1 if request.form.get(f"{prefix}_eliminar") else 0
            exportar = 1 if request.form.get(f"{prefix}_exportar") else 0
        cursor.execute("SELECT 1 FROM PermisoModulo WHERE usuario_id = ? AND modulo_id = ?", (usuario_id, modulo_id))
        existe = cursor.fetchone()
        if existe:
            cursor.execute(
                """
                UPDATE PermisoModulo 
                SET ver=?, crear=?, editar=?, eliminar=?, exportar=?
                WHERE usuario_id=? AND modulo_id=?
                """,
                (ver, crear, editar, eliminar, exportar, usuario_id, modulo_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar),
            )
    conn.commit()
    conn.close()
    if usuario_id == session["id_usuario"]:
        cargar_permisos_en_sesion(usuario_id)
    flash("Permisos actualizados correctamente", "success")
    return redirect(url_for("configuracion.editar_usuario", usuario_id=usuario_id))

# ---------------------------------------------------------------------------
# Agregar usuario
@configuracion_bd.route("/agregar_usuario", methods=["GET", "POST"])
def agregar_usuario():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        rol = request.form.get("rol", "2")
        password_hash = generate_password_hash(contraseña)
        conn = conection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Usuario (nombre_u, password, rol_id) VALUES (?, ?, ?)", (nombre, password_hash, rol)
        )
        usuario_id = cursor.lastrowid
        cursor.execute("SELECT id_modulo FROM Modulo")
        modulos = cursor.fetchall()
        es_admin = rol == "1"
        for modulo in modulos:
            modulo_id = modulo[0]
            if es_admin:
                cursor.execute(
                    """
                    INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                    VALUES (?, ?, 1, 1, 1, 1, 1)
                    """,
                    (usuario_id, modulo_id),
                )
            else:
                if modulo_id == 7:
                    continue
                if modulo_id == 1:
                    valores = (1, 1, 0, 0, 0)
                else:
                    valores = (1, 0, 0, 0, 0)
                cursor.execute(
                    """
                    INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (usuario_id, modulo_id, *valores),
                )
        conn.commit()
        conn.close()
        flash("Usuario creado correctamente con permisos por módulo.", "success")
        return redirect(url_for("configuracion.index"))
    return render_template("AgregarUsuario.html", title="Agregar Usuario")

# ---------------------------------------------------------------------------
# Seguridad (lista de usuarios para cambiar contraseña)
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

# ---------------------------------------------------------------------------
# Cambiar contraseña
@configuracion_bd.route("/cambiar_contrasena", methods=["POST"])
def cambiar_contrasena():
    if not session.get("permisos", {}).get("administrar_sistema"):
        return "Acceso denegado", 403
    usuario_id = request.form.get("usuario_id")
    nueva = request.form.get("nueva")
    if not usuario_id or not nueva:
        return "Faltan datos", 400
    if len(nueva) < 8:
        return "La contraseña debe tener al menos 8 caracteres", 400
    password_hash = generate_password_hash(nueva)
    try:
        conn = conection()
        conn.execute("UPDATE Usuario SET password = ? WHERE id_usuario = ?", (password_hash, usuario_id))
        conn.commit()
        conn.close()
        return "OK"
    except Exception as e:
        print("Error al cambiar contraseña:", e)
        return "Error en el servidor", 500

# ---------------------------------------------------------------------------
# Eliminar usuario
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
    cursor.execute("DELETE FROM PermisoModulo WHERE usuario_id = ?", (usuario_id,))
    cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?", (usuario_id,))
    conn.commit()
    conn.close()
    flash("Usuario eliminado correctamente.")
    return redirect(url_for("configuracion.index"))

# ---------------------------------------------------------------------------
# Editar usuario (incluye permisos y seguridad sections)
@configuracion_bd.route("/editar_usuario/<int:usuario_id>", methods=["GET", "POST"])
def editar_usuario(usuario_id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    conn = conection()
    if request.method == "POST":
        nombre = request.form["nombre"]
        rol = request.form.get("rol", "2")
        conn.execute("UPDATE Usuario SET nombre_u = ?, rol_id = ? WHERE id_usuario = ?", (nombre, rol, usuario_id))
        conn.commit()
        conn.close()
        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for("configuracion.index"))
    # GET: mostrar formulario y datos de permisos
    usuario = conn.execute("SELECT * FROM Usuario WHERE id_usuario = ?", (usuario_id,)).fetchone()
    modulos = conn.execute("SELECT id_modulo, nombre_modulo, clave_modulo FROM Modulo ORDER BY nombre_modulo").fetchall()
    permisos_db = conn.execute("SELECT modulo_id, ver, crear, editar, eliminar, exportar FROM PermisoModulo WHERE usuario_id = ?", (usuario_id,)).fetchall()
    permisos_dict = {}
    for p in permisos_db:
        mid = p[0]
        permisos_dict[mid] = {"ver": p[1], "crear": p[2], "editar": p[3], "eliminar": p[4], "exportar": p[5]}
    conn.close()
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("configuracion.index"))
    return render_template("EditarUsuario.html", usuario=usuario, modulos=modulos, permisos=permisos_dict, title="Editar Usuario")
