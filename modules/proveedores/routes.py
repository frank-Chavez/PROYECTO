from flask import Blueprint, render_template, redirect, url_for, request, send_file, session
from database import conection
import pandas as pd
import io
from decoradores import permiso_requerido

proveedor_bd = Blueprint(
    "proveedor", __name__, url_prefix="/proveedor", template_folder="templates", static_folder="static"
)


@proveedor_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    proveedor = conn.execute("SELECT * FROM Proveedores").fetchall()
    conn.close()
    return render_template("proveedor.html", proveedor=proveedor, title="Proveedor")


@proveedor_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        proveedor = conn.execute(
            """SELECT * FROM Proveedores 
            WHERE LOWER(remove_acentos(nombre_p)) LIKE ?
            OR LOWER(remove_acentos(servicio_p)) LIKE ?""",
            (f"%{search.lower()}%", f"%{search.lower()}%"),
        ).fetchall()
        conn.close()
        return render_template("proveedor.html", proveedor=proveedor, busqueda=search, title="Proveedor")
    return redirect(url_for("proveedor.listar"))


@proveedor_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
@permiso_requerido("eliminar_registros")
def cambiar_estado(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    proveedor = conn.execute("SELECT estado_p FROM Proveedores WHERE id_proveedor = ?", (id,)).fetchone()

    if proveedor:
        nuevo_estado = 0 if proveedor["estado_p"] == 1 else 1
        conn.execute("UPDATE Proveedores SET estado_p = ? WHERE id_proveedor = ?", (nuevo_estado, id))
        conn.commit()

    conn.close()
    return redirect(url_for("proveedor.listar"))


@proveedor_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("editar_registros")
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        nombreProveedor = request.form["nombre_p"]
        telefono = request.form["telefono_p"]
        correo = request.form["correo_p"]
        servicio = request.form["servicio_p"]
        fechaRegistro = request.form["fechaRegistro_p"]
        estado = request.form["estado_p"]

        conn.execute(
            """
                UPDATE Proveedores 
                SET nombre_p = ?, telefono_p = ?, correo_p = ?, servicio_p = ?, fechaRegistro_p = ?, estado_p    = ?
                WHERE id_proveedor = ?
            """,
            (nombreProveedor, telefono, correo, servicio, fechaRegistro, estado, id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("proveedor.listar"))

    editar = conn.execute(
        """
        SELECT id_proveedor, nombre_p, telefono_p, correo_p, servicio_p, fechaRegistro_p, estado_p  
        FROM Proveedores 
        WHERE id_proveedor = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    return render_template("editar_proveedor.html", Proveedor=editar, title="Registrar proveedor")


@proveedor_bd.route("/VerDetalles/<int:id>", methods=["GET"])
@permiso_requerido("ver_registros")
def VerDetalles(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    proveedor = conn.execute(
        """
        SELECT id_proveedor, nombre_p, telefono_p, correo_p, servicio_p, fechaRegistro_p, estado_p  
        FROM Proveedores 
        WHERE id_proveedor = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    if not proveedor:
        return "proveedor no encontrado", 404

    return render_template("detalles_proveedores.html", proveedor=proveedor, title="Detalles del proveedor")


@proveedor_bd.route("/agregar", methods=["GET", "POST"], endpoint="agregar")
@permiso_requerido("crear_registros")
def agregar_fallecido():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["Telefono"]
        correo = request.form["correo"]
        servicio = request.form["servicio"]
        fechaRegistro = request.form["fechaRegistro"]
        estado = request.form["estado"]

        conn = conection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Proveedores (
                nombre_p, telefono_p, correo_p, servicio_p, fechaRegistro_p, estado_p
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (nombre, telefono, correo, servicio, fechaRegistro, estado),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("proveedor.listar"))

    return render_template("agregar_proveedor.html", title="Proveedor")


@proveedor_bd.route("/exel")
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
            p.nombre_p AS 'Nombre del Proveedor',
            p.telefono_p AS 'Teléfono del Proveedor',
            p.correo_p AS 'Correo del Proveedor',
            p.servicio_p AS 'Servicio del Proveedor',
            p.fechaRegistro_p AS 'Fecha de Registro',
            CASE 
                WHEN p.estado_p = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Proveedores p
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Proveedores")

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="Proveedores.xlsx",
            as_attachment=True,
        )

    except Exception as e:
        import traceback

        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500
