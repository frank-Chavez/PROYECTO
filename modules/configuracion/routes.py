from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from database import conection
from werkzeug.security import generate_password_hash


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

    # Obtener todos los usuarios
    usuarios = conn.execute("SELECT id_usuario, nombre_u FROM Usuario ORDER BY nombre_u").fetchall()

    # Obtener todos los módulos
    modulos = conn.execute(
        "SELECT id_modulo, nombre_modulo, clave_modulo FROM Modulo ORDER BY nombre_modulo"
    ).fetchall()

    # Obtener todos los permisos existentes
    permisos_db = conn.execute(
        """
        SELECT usuario_id, modulo_id, ver, crear, editar, eliminar, exportar 
        FROM PermisoModulo
    """
    ).fetchall()

    # Convertir a diccionario para fácil acceso en la plantilla
    permisos_dict = {}
    for p in permisos_db:
        if p[0] not in permisos_dict:
            permisos_dict[p[0]] = {}
        permisos_dict[p[0]][p[1]] = {"ver": p[2], "crear": p[3], "editar": p[4], "eliminar": p[5], "exportar": p[6]}

    conn.close()

    return render_template(
        "permisos.html", usuarios=usuarios, modulos=modulos, permisos=permisos_dict, title="Permisos por Módulo"
    )


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
        permisos_dict[clave] = {
            "ver": bool(p[1]),
            "crear": bool(p[2]),
            "editar": bool(p[3]),
            "eliminar": bool(p[4]),
            "exportar": bool(p[5]),
        }

    session["permisos"] = permisos_dict


@configuracion_bd.route("/guardar_permisos_modulo", methods=["POST"])
def guardar_permisos_modulo():
    if "id_usuario" not in session or not session["permisos"].get("administrar_sistema"):
        return redirect(url_for("login"))

    usuario_id = int(request.form["usuario_id"])

    # Proteger al admin principal (id = 1)
    if usuario_id == 1:
        flash("No puedes modificar los permisos del administrador principal.", "error")
        return redirect(url_for("configuracion.permisos"))

    conn = conection()
    cursor = conn.cursor()

    # ID real del módulo configuración
    ID_MODULO_CONFIGURACION = 7

    # Obtener todos los módulos
    modulos = cursor.execute("SELECT id_modulo, clave_modulo FROM Modulo").fetchall()

    for modulo in modulos:
        modulo_id = modulo[0]

        # === MÓDULO ESPECIAL: Configuración (id = 7) ===
        if modulo_id == ID_MODULO_CONFIGURACION:
            # Viene del switch grande del template
            tiene_acceso = request.form.get("acceso_configuracion") == "1"
            ver = crear = editar = eliminar = exportar = 1 if tiene_acceso else 0
        else:
            # Módulos normales
            prefix = f"modulo_{modulo_id}"
            ver = 1 if request.form.get(f"{prefix}_ver") else 0
            crear = 1 if request.form.get(f"{prefix}_crear") else 0
            editar = 1 if request.form.get(f"{prefix}_editar") else 0
            eliminar = 1 if request.form.get(f"{prefix}_eliminar") else 0
            exportar = 1 if request.form.get(f"{prefix}_exportar") else 0

        # Insertar o actualizar
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

    # Recargar permisos en sesión si es el usuario actual
    if usuario_id == session["id_usuario"]:
        cargar_permisos_en_sesion(usuario_id)

    flash("Permisos actualizados correctamente", "success")
    return redirect(url_for("configuracion.permisos") + f"#user{usuario_id}")


@configuracion_bd.route("/agregar_usuario", methods=["GET", "POST"])
def agregar_usuario():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        contraseña = request.form["contraseña"]
        rol = request.form.get("rol", "2")  # por defecto no admin

        password_hash = generate_password_hash(contraseña)

        conn = conection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO Usuario (nombre_u, password, rol_id) VALUES (?, ?, ?)", (nombre, password_hash, rol)
        )
        usuario_id = cursor.lastrowid

        # --- NUEVO: Dar permisos por módulo ---
        cursor.execute("SELECT id_modulo FROM Modulo")
        modulos = cursor.fetchall()

        es_admin = rol == "1"  # si el rol 1 es administrador

        for modulo in modulos:
            modulo_id = modulo[0]
            if es_admin:
                # Admin tiene todo
                cursor.execute(
                    """
                    INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                    VALUES (?, ?, 1, 1, 1, 1, 1)
                """,
                    (usuario_id, modulo_id),
                )
            else:
                # Usuario normal: solo ver y crear en algunos módulos (tú decides)
                # Ejemplo: solo ver cotizaciones y crear cotizaciones
                if modulo_id == 1:  # Supongamos que 1 = cotizaciones
                    cursor.execute(
                        """
                        INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                        VALUES (?, ?, 1, 1, 0, 0, 0)
                    """,
                        (usuario_id, modulo_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO PermisoModulo (usuario_id, modulo_id, ver, crear, editar, eliminar, exportar)
                        VALUES (?, ?, 1, 0, 0, 0, 0)
                    """,
                        (usuario_id, modulo_id),
                    )

        conn.commit()
        conn.close()
        flash("Usuario creado correctamente con permisos por módulo.")
        return redirect(url_for("configuracion.index"))

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

    # ← ELIMINAR DE LA TABLA NUEVA
    cursor.execute("DELETE FROM PermisoModulo WHERE usuario_id = ?", (usuario_id,))
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


@configuracion_bd.route("/cambiar_contrasena", methods=["POST"])
def cambiar_contrasena():
    # Protección: solo admin o quien tenga permiso
    if not session.get("permisos", {}).get("administrar_sistema"):
        return "Acceso denegado", 403

    usuario_id = request.form.get("usuario_id")
    nueva = request.form.get("nueva")

    if not usuario_id or not nueva:
        return "Faltan datos", 400

    if len(nueva) < 8:
        return "La contraseña debe tener al menos 8 caracteres", 400

    # Hashear la nueva contraseña
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
