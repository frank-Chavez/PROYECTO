from flask import Blueprint, render_template, redirect, url_for, request, send_file, session
from database import conection
import pandas as pd
import io
from decoradores import permiso_requerido

familiares_bd = Blueprint(
    "familiares", __name__, url_prefix="/familiares", template_folder="templates", static_folder="static"
)


@familiares_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page - 1) * per_page

    cursor.execute("SELECT COUNT(*) AS total FROM Familiares")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT * FROM Familiares LIMIT ? OFFSET ?", (per_page, offset))
    familiares = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "familiares.html",
        title="Familiares",
        familiares=familiares,
        page=page,
        total=total,
        per_page=per_page,
        total_pages=total_pages,
    )


@familiares_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        familiares = conn.execute(
            """
            SELECT * FROM Familiares
            WHERE LOWER(remove_acentos(f_nombre)) LIKE ?
            OR LOWER(remove_acentos(f_apellido)) LIKE ?
            """,
            (f"%{search}%", f"%{search}%"),
        ).fetchall()

        conn.close()
        return render_template(
            "familiares.html",
            familiares=familiares,
            busqueda=search,
            page=1,
            total=len(familiares),
            per_page=len(familiares),
            total_pages=1,
            title="Familiares",
        )
    return redirect(url_for("familiares.listar"))


@familiares_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
@permiso_requerido("eliminar_registros")
def cambiar_estado(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    familiares = conn.execute("SELECT f_estado FROM Familiares WHERE id_familiar = ?", (id,)).fetchone()

    if familiares:
        nuevo_estado = 0 if familiares["f_estado"] == 1 else 1
        conn.execute("UPDATE Familiares SET f_estado = ? WHERE id_familiar = ?", (nuevo_estado, id))
        conn.commit()

    conn.close()
    return redirect(url_for("familiares.listar"))


@familiares_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("editar_registros")
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        nombre = request.form["f_nombre"]
        apellido = request.form["f_apellido"]
        parentesco = request.form["f_parentesco"]
        telefono = request.form["f_telefono"]
        correo = request.form["f_correo"]
        estado = request.form["f_estado"]
        fechaRegistro = request.form["fechaRegistro"]

        conn.execute(
            """
                UPDATE Familiares 
                SET f_nombre = ?, f_apellido = ?, f_parentesco = ?, f_telefono = ?, f_correo = ?, f_estado = ?, fechaRegistro = ?
                WHERE id_familiar = ?
            """,
            (nombre, apellido, parentesco, telefono, correo, estado, fechaRegistro, id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("familiares.listar"))

    editar = conn.execute(
        """
        SELECT id_familiar, f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, f_estado, fechaRegistro 
        FROM Familiares 
        WHERE id_familiar = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    return render_template("editar.html", familiar=editar)


@familiares_bd.route("/VerDetalles/<int:id>", methods=["GET"])
@permiso_requerido("ver_registros")
def VerDetalles(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    familiar = conn.execute(
        """
        SELECT id_familiar, f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, fechaRegistro, f_estado
        FROM Familiares 
        WHERE id_familiar = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    if not familiar:
        return "Familiar no encontrado", 404

    return render_template("detalles_familiares.html", familiar=familiar, title="Detalles del Familiar")


@familiares_bd.route("/agregar", methods=["GET", "POST"], endpoint="agregar")
@permiso_requerido("crear_registros")
def agregar_familiar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        parentesco = request.form["parentesco"]
        telefono = request.form["telefono"]
        correo = request.form["correo"]
        estado = request.form["estado"]
        fechaRegistro = request.form["fechaRegistro"]

        usuario_id = 1  # ajusta según tu lógica de login

        conn = conection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Familiares (
                f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, f_estado, fechaRegistro, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (nombre, apellido, parentesco, telefono, correo, estado, fechaRegistro, usuario_id),
        )
        conn.commit()
        conn.close()

        # Aquí el cambio: redirige a la lista de familiares
        return redirect(url_for("familiares.listar"))

    return render_template("agregar_familiar.html", title="Familiar")


@familiares_bd.route("/exel")
@permiso_requerido("exportar_datos")
def exel():
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    try:
        # coneccion a la bd
        conn = conection()
        # consultando la informacion que se va a descargar
        consulta = """
        SELECT 
            f.f_nombre || ' ' || f.f_apellido AS 'Nombre del Familiar',
            f.f_parentesco AS 'Parentesco',
            f.f_telefono AS 'Teléfono',
            f.f_correo AS 'Correo',
            REPLACE(f.fechaRegistro, '-','/')  AS 'Fecha de registro',
            CASE 
                WHEN f.f_estado = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Familiares f
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Familiares")

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="Familiares.xlsx",
            as_attachment=True,
        )

    except Exception as e:
        import traceback

        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500
