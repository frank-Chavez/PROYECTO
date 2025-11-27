from flask import Blueprint, render_template, redirect, url_for, request, send_file, session
from database import conection
import pandas as pd
import io
from decoradores import permiso_requerido

servicios_bd = Blueprint(
    "servicios", __name__, url_prefix="/servicios", template_folder="templates", static_folder="static"
)


@servicios_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page - 1) * per_page

    cursor.execute("SELECT COUNT(*) AS total FROM Servicios")
    total = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT 
            s.id_servicio,
            s.tipo_serv,
            s.descripcion_serv,
            s.categoria_serv,
            s.precio_serv,
            p.nombre_p,
            s.estado_serv
        FROM Servicios s
        LEFT JOIN Proveedores p 
        ON s.proveedor_id = p.id_proveedor
        ORDER BY s.id_servicio DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    )
    servicios = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "servicios.html",
        title="Servicios",
        servicios=servicios,
        page=page,
        total=total,
        per_page=per_page,
        total_pages=total_pages,
    )


@servicios_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        servicios = conn.execute(
            """SELECT 
                s.id_servicio,
                s.tipo_serv,
                s.descripcion_serv,
                s.categoria_serv,
                s.precio_serv,
                p.nombre_p,
                s.estado_serv
            FROM Servicios s
            JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
            WHERE LOWER(remove_acentos(s.tipo_serv)) LIKE ?
            OR LOWER(remove_acentos(p.nombre_p)) LIKE ?""",
            (f"%{search.lower()}%", f"%{search.lower()}%"),
        ).fetchall()

        conn.close()
        return render_template(
            "servicios.html",
            servicios=servicios,
            busqueda=search,
            page=1,
            total=len(servicios),
            per_page=len(servicios),
            total_pages=1,
            title="Servicios",
        )
    return redirect(url_for("servicios.listar"))


@servicios_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
@permiso_requerido("servicios", "eliminar")
def cambiar_estado(id):

    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    servicios = conn.execute("SELECT estado_serv FROM Servicios WHERE id_servicio = ?", (id,)).fetchone()

    if servicios:
        nuevo_estado = 0 if servicios["estado_serv"] == 1 else 1
        conn.execute("UPDATE Servicios SET estado_serv = ? WHERE id_servicio = ?", (nuevo_estado, id))
        conn.commit()

    conn.close()
    return redirect(url_for("servicios.listar"))


@servicios_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("servicios", "editar")
def editar(id):

    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cursor = conn.cursor()

    # Traer proveedores activos
    cursor.execute("SELECT id_proveedor, nombre_p FROM Proveedores WHERE estado_p=1")
    proveedores = cursor.fetchall()

    if request.method == "POST":
        tipo_serv = request.form["tipo_serv"]
        descripcion = request.form["descripcion_serv"]
        categoria = request.form["categoria_serv"]
        precio_serv = float(request.form["precio_serv"])
        proveedor_id = int(request.form["proveedor_id"])
        estado_serv = int(request.form["estado_serv"])

        cursor.execute(
            """
            UPDATE Servicios 
            SET tipo_serv = ?, descripcion_serv = ?, categoria_serv = ?, precio_serv = ?, proveedor_id = ?, estado_serv = ?
            WHERE id_servicio = ?
            """,
            (tipo_serv, descripcion, categoria, precio_serv, proveedor_id, estado_serv, id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("servicios.listar"))

    # Obtener datos del servicio a editar
    editar = cursor.execute(
        """
        SELECT 
            s.id_servicio,
            s.tipo_serv,
            s.descripcion_serv,
            s.categoria_serv,
            s.precio_serv,
            s.proveedor_id,
            s.estado_serv,
            p.nombre_p
        FROM Servicios s
        LEFT JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
        WHERE s.id_servicio = ?
        """,
        (id,),
    ).fetchone()
    conn.close()

    return render_template("editar_servicios.html", servicioss=editar, proveedores=proveedores, title="Editar Servicio")


@servicios_bd.route("/VerDetalles/<int:id>", methods=["GET"])
@permiso_requerido("servicios", "ver")
def VerDetalles(id):

    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    servicio = conn.execute(
        """
        SELECT s.id_servicio,
               s.tipo_serv,
               s.descripcion_serv,
               s.categoria_serv,
               s.precio_serv,
               p.nombre_p,
               s.estado_serv
        FROM Servicios s
        LEFT JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
        WHERE s.id_servicio = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    if not servicio:
        return "Servicio no encontrado", 404

    return render_template("detalles_servicio.html", servicio=servicio, title="Detalles del Servicio")


@servicios_bd.route("/agregar", methods=["GET", "POST"], endpoint="agregar")
@permiso_requerido("servicios", "crear")
def agregar_servicio():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cursor = conn.cursor()
    # Traer proveedores activos para el select
    cursor.execute("SELECT id_proveedor, nombre_p FROM Proveedores WHERE estado_p=1")
    proveedores = cursor.fetchall()

    if request.method == "POST":
        tipoServ = request.form["tipoServ"]
        descripcionServ = request.form["descripcionServ"]
        categoriaServ = request.form["categoriaServ"]
        precio_serv = float(request.form["precio_serv"])
        estado = int(request.form["estado"])
        proveedor_id = int(request.form["proveedor_id"])

        cursor.execute(
            """
            INSERT INTO Servicios (
                tipo_serv, descripcion_serv, categoria_serv, precio_serv, proveedor_id, estado_serv
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tipoServ, descripcionServ, categoriaServ, precio_serv, proveedor_id, estado),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("servicios.listar"))

    conn.close()
    return render_template("agregar_servicio.html", title="Servicio", proveedores=proveedores)


@servicios_bd.route("/exel")
@permiso_requerido("servicios", "exportar")
def exel():

    if "id_usuario" not in session:
        return redirect(url_for("login"))

    try:
        # coneccion a la bd
        conn = conection()
        # consultando la informacion que se va a descargar
        consulta = """
        SELECT 
            s.tipo_serv AS 'Tipo de servicio',
            s.descripcion_serv AS 'Descripción',
            s.categoria_serv AS 'Categoría',
            s.precio_serv AS 'Precio (S/)',
            p.nombre_p AS 'Proveedor',
            CASE 
                WHEN s.estado_serv = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Servicios s
        LEFT JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Servicios")

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="servicios.xlsx",
            as_attachment=True,
        )

    except Exception as e:
        import traceback

        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500
