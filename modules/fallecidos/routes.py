from flask import Blueprint, render_template, redirect, url_for, request, send_file, session
from database import conection
import pandas as pd
import io
from decoradores import permiso_requerido

fallecidos_bd = Blueprint(
    "fallecidos", __name__, url_prefix="/fallecidos", template_folder="templates", static_folder="static"
)


@fallecidos_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    fallecidos = conn.execute("SELECT * FROM Fallecidos").fetchall()
    conn.close()
    return render_template("fallecidos.html", Fallecidos=fallecidos, title="Fallecidos")


@fallecidos_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        fallecidos = conn.execute(
            """SELECT * FROM Fallecidos 
            WHERE LOWER(remove_acentos(nombre_f)) LIKE ?""",
            ("%" + search + "%",),
        ).fetchall()
        conn.close()
        return render_template("fallecidos.html", Fallecidos=fallecidos, busqueda=search, title="Fallecidos")
    return redirect(url_for("fallecidos.listar"))


@fallecidos_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
@permiso_requerido("eliminar_registros")
def cambiar_estado(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    fallecido = conn.execute("SELECT estado_f FROM Fallecidos WHERE id_fallecido = ?", (id,)).fetchone()

    if fallecido:
        nuevo_estado = 0 if fallecido["estado_f"] == 1 else 1
        conn.execute("UPDATE Fallecidos SET estado_f = ? WHERE id_fallecido = ?", (nuevo_estado, id))
        conn.commit()

    conn.close()
    return redirect(url_for("fallecidos.listar"))


@fallecidos_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("editar_registros")
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        nombre = request.form["nombre_f"]
        edad = request.form["edad_f"]
        fechaDefuncion = request.form["fecha_defuncion"]
        fechaRegistro = request.form["fechaRegistro_f"]
        fechaActualizacion = request.form["fechaActualizacion_f"]
        estado = request.form["estado_f"]

        conn.execute(
            """
                UPDATE Fallecidos 
                SET nombre_f = ?, edad_f = ?, fecha_defuncion = ?, fechaRegistro_f = ?, fechaActualizacion_f = ?, estado_f = ?
                WHERE id_fallecido = ?
            """,
            (nombre, edad, fechaDefuncion, fechaRegistro, fechaActualizacion, estado, id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("fallecidos.listar"))

    editar = conn.execute(
        """
        SELECT id_fallecido, nombre_f, edad_f, fecha_defuncion, fechaRegistro_f, fechaActualizacion_f, estado_f
        FROM Fallecidos 
        WHERE id_fallecido = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    return render_template("editar_fallecido.html", fallecidos=editar, title="Registrar Fallecido")


@fallecidos_bd.route("/VerDetalles/<int:id>", methods=["GET"])
@permiso_requerido("ver_registros")
def VerDetalles(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    fallecidos = conn.execute(
        """
        SELECT id_fallecido, nombre_f, edad_f, fecha_defuncion, fechaRegistro_f, fechaActualizacion_f, estado_f
        FROM Fallecidos 
        WHERE id_fallecido = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    if not fallecidos:
        return "fallecido no encontrado", 404

    return render_template("detalles_fallecidos.html", fallecidos=fallecidos, title="Detalles del fallecido")


@fallecidos_bd.route("/agregar", methods=["GET", "POST"], endpoint="agregar")
@permiso_requerido("crear_registros")
def agregar_fallecido():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        fechaDefuncion = request.form["fechaDefuncion"]
        estado = request.form["estado"]
        edad = request.form["edad"]
        estado = request.form["estado"]
        fechaRegistro = request.form["fechaRegistro"]

        conn = conection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Fallecidos (
                nombre_f, fecha_defuncion, estado_f, edad_f, fechaRegistro_f
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (nombre, fechaDefuncion, estado, edad, fechaRegistro),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("fallecidos.listar"))

    return render_template("agregar_fallecido.html", title="Fallecido")


@fallecidos_bd.route("/exel")
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
            f.nombre_f AS 'Nombre del Fallecido',
            REPLACE(f.fecha_defuncion, '-','/')  AS 'Fecha de Defuncion',
            f.edad_f AS 'Edad',
            REPLACE(f.fechaRegistro_f, '-','/')  AS 'Fecha de Registro',
            REPLACE(f.fechaActualizacion_f, '-','/')  AS 'Fecha de Actualizacion',
            f.estado_f AS 'Estado',

            CASE 
                WHEN f.estado_f = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Fallecidos f
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Fallecidos")

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="Fallecidos.xlsx",
            as_attachment=True,
        )

    except Exception as e:
        import traceback

        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500
