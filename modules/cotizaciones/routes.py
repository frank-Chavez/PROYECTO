from flask import (
    Response,
    request,
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
)
from datetime import date
from database import conection
from weasyprint import HTML
import io
from datetime import date
from decoradores import permiso_requerido

cotizaciones_bd = Blueprint(
    "cotizacion",
    __name__,
    url_prefix="/cotizacion",
    template_folder="templates",
    static_folder="static",
)


# ----------------------------------------Tabla principal de cotizaciones----------------------------------------
@cotizaciones_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    # Parámetros de paginación
    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page - 1) * per_page

    # Total de registros
    cursor.execute("SELECT COUNT(*) AS total FROM Cotizacion")
    total = cursor.fetchone()["total"]

    # Consulta con JOIN (no LEFT JOIN)
    cursor.execute(
        """
        SELECT
            c.id_cotizacion,
            c.numero_cot,
            c.fecha_cot,
            c.monto_cot,
            c.validacion_cot,
            c.estado_cot,
            f.f_nombre,
            f.f_apellido
        FROM Cotizacion c
        JOIN cotizacion_detalles d ON c.id_cotizacion = d.id_cotizacion
        JOIN Familiares f ON d.id_familiar = f.id_familiar
        ORDER BY c.id_cotizacion DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    )
    cotizacion = cursor.fetchall()
    cursor.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "cotizacion.html",
        title="Cotizaciones",
        cotizacion=cotizacion,
        page=page,
        total=total,
        per_page=per_page,
        total_pages=total_pages,
    )


# ----------------------------------------Opcion de busqueda----------------------------------------
@cotizaciones_bd.route("/busador", methods=["GET", "POST"])
def buscador():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        search = request.form["buscar"]
        conn = conection()
        cotizacion = conn.execute(
            """
            SELECT 
                c.id_cotizacion,
                c.numero_cot,
                c.fecha_cot,
                c.monto_cot,
                c.validacion_cot,
                c.estado_cot,
                f.f_nombre,
                f.f_apellido
            FROM Cotizacion c
            JOIN cotizacion_detalles d ON c.id_cotizacion = d.id_cotizacion
            JOIN Familiares f ON d.id_familiar = f.id_familiar
            WHERE LOWER(remove_acentos(f.f_nombre)) LIKE ?
            """,
            ("%" + search + "%",),
        ).fetchall()

        conn.close()
        return render_template(
            "cotizacion.html",
            cotizacion=cotizacion,
            busqueda=search,
            page=1,
            total=len(cotizacion),
            per_page=len(cotizacion),
            total_pages=1,
            title="Cotizaciones",
        )
    return redirect(url_for("cotizacion.listar"))


# ----------------------------------------Opcion de cambiar el estado----------------------------------------
@cotizaciones_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "eliminar")
def cambiar_estado(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cotizaciones = conn.execute("SELECT estado_cot FROM Cotizacion WHERE id_cotizacion = ?", (id,)).fetchone()

    if cotizaciones:
        nuevo_estado = 0 if cotizaciones["estado_cot"] == 1 else 1
        conn.execute(
            "UPDATE Cotizacion SET estado_cot = ? WHERE id_cotizacion = ?",
            (nuevo_estado, id),
        )
        conn.commit()

    conn.close()
    return redirect(url_for("cotizacion.listar"))


# ----------------------------------------Opcion de editar----------------------------------------
@cotizaciones_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("cotizacion", "editar")
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        numerocot = request.form["numero_cot"]
        fechacot = request.form["fecha_cot"]
        montocot = request.form["monto_cot"]
        validacioncot = request.form["validacion_cot"]
        estado = request.form["estado_cot"]
        plan_seleccionado = request.form.get("plan_cremacion")
        servicios_seleccionadoss = request.form.getlist("servicios_adicionales")
        familiares_seleccionados = request.form.getlist("nombre_cliente")

        # Actualizar cotizacion principal (ahora con el orden correcto)
        conn.execute(
            """
            UPDATE Cotizacion 
            SET numero_cot = ?, fecha_cot = ?, monto_cot = ?, validacion_cot = ?, estado_cot = ?
            WHERE id_cotizacion = ?
        """,
            (numerocot, fechacot, montocot, validacioncot, estado, id),
        )

        # Primero eliminamos los detalles antiguos
        conn.execute("DELETE FROM cotizacion_detalles WHERE id_cotizacion = ?", (id,))

        # Insertamos el plan seleccionado
        if plan_seleccionado:
            conn.execute(
                """
                INSERT INTO cotizacion_detalles (id_cotizacion, id_plan)
                VALUES (?, ?)
            """,
                (id, int(plan_seleccionado)),
            )

        # Insertamos familiares seleccionados
        for f_id in familiares_seleccionados:
            conn.execute(
                """
                INSERT INTO cotizacion_detalles (id_cotizacion, id_familiar)
                VALUES (?, ?)
            """,
                (id, int(f_id)),
            )

        # Insertamos servicios seleccionados (ahora con cantidad)
        for s_id in servicios_seleccionadoss:
            cantidad = request.form.get(f"cantidad_servicio[{s_id}]", 1)
            conn.execute(
                """
                INSERT INTO cotizacion_detalles (id_cotizacion, id_servicio, cantidad)
                VALUES (?, ?, ?)
            """,
                (id, int(s_id), int(cantidad)),
            )

        conn.commit()
        conn.close()
        return redirect(url_for("cotizacion.listar"))

    # GET: Traemos cotizacion principal
    cotizacion = conn.execute(
        """
        SELECT * FROM Cotizacion WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()

    # Traemos plan asociado
    plan = conn.execute(
        """
        SELECT p.id_plan, p.tipo_plan, precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ?
    """,
        (id,),
    ).fetchone()

    # Traemos servicios asociados
    servicios = conn.execute(
        """
        SELECT s.id_servicio, s.tipo_serv, precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ?
    """,
        (id,),
    ).fetchall()

    servicios_cantidades = {s["id_servicio"]: s["cantidad"] for s in servicios}

    # Traemos familiares asociados
    familiares = conn.execute(
        """
        SELECT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ?
    """,
        (id,),
    ).fetchall()

    # Traemos todas las opciones para mostrar en el form
    planes_disponibles = conn.execute(
        "SELECT id_plan, tipo_plan, precio_plan FROM Planes WHERE estado_plan=1"
    ).fetchall()
    servicios_disponibles = conn.execute(
        "SELECT id_servicio, tipo_serv, precio_serv FROM Servicios WHERE estado_serv=1"
    ).fetchall()
    familiares_disponibles = conn.execute(
        "SELECT id_familiar, f_nombre, f_apellido FROM Familiares WHERE f_estado=1"
    ).fetchall()

    conn.close()
    return render_template(
        "editar_Cotizaciones.html",
        cot=cotizacion,
        plan=plan,
        servicios=servicios,
        servicios_cantidades=servicios_cantidades,
        familiares=familiares,
        planes_disponibles=planes_disponibles,
        servicios_disponibles=servicios_disponibles,
        familiares_disponibles=familiares_disponibles,
        title="Editar Cotización",
    )


# ----------------------------------------Opcion para ver los detalles o informacion----------------------------------------
@cotizaciones_bd.route("/VerDetalles/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "ver")
def VerDetalles(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    conn = conection()
    cur = conn.cursor()

    # Cotizacion principal :)
    cotizacion = cur.execute(
        """
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()
    if not cotizacion:
        conn.close()
        return "cotizacion no encontrado", 404

    # Obtener el plan asociado
    plan = cur.execute(
        """
        SELECT p.id_plan, p.tipo_plan, p.precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
    """,
        (id,),
    ).fetchone()

    # Obtener los servicios asociados
    servicios = cur.execute(
        """
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """,
        (id,),
    ).fetchall()

    # Obtener los familiares asociados
    familiares = cur.execute(
        """
        SELECT DISTINCT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ? AND cd.id_familiar IS NOT NULL
    """,
        (id,),
    ).fetchall()

    conn.close()
    return render_template(
        "detalles_cotizaciones.html",
        cotizacion=cotizacion,
        plan=plan,
        servicios=servicios,
        familiares=familiares,
        title="Detalles del cotizacion",
    )


# ----------------------------------------Opcion de agregar informacion----------------------------------------
@cotizaciones_bd.route("/agregar", methods=["GET", "POST"])
@permiso_requerido("cotizacion", "crear")
def agregar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    with conection() as conn:
        cur = conn.cursor()

        # Obtener último número de cotización
        ultimo = cur.execute("SELECT numero_cot FROM Cotizacion ORDER BY id_cotizacion DESC LIMIT 1").fetchone()
        if ultimo and ultimo["numero_cot"]:
            try:
                numero = int(ultimo["numero_cot"].split("-")[1])
            except:
                numero = 0
            new_num = numero + 1
        else:
            new_num = 1
        numero_cot = f"COT-{new_num:03d}"

        # Obtener planes, servicios y familiares activos
        cur.execute("SELECT id_plan, tipo_plan, precio_plan FROM Planes WHERE estado_plan = '1'")
        planes = cur.fetchall()
        cur.execute("SELECT id_servicio, tipo_serv, precio_serv FROM Servicios WHERE estado_serv = '1'")
        servicios = cur.fetchall()
        cur.execute("SELECT id_familiar, f_nombre, f_apellido FROM Familiares WHERE f_estado = '1'")
        familiares = cur.fetchall()

        if request.method == "POST":
            fecha_cot = request.form.get("fecha_cot")
            monto_cot = request.form.get("monto_cot")
            validacion_cot = "Aprobada"
            estado_cot = 1
            planes_seleccionado = request.form.get("plan_cremacion")
            servicios_seleccionados = request.form.getlist("servicio_adicional")
            familiares_seleccionado = request.form.getlist("nombre_cliente")

            # Validación: campos obligatorios
            if not monto_cot:
                return render_template(
                    "agregar_cotizacion.html",
                    title="Agregar Cotización",
                    error="Completa todos los campos.",
                    planes=planes,
                    servicios=servicios,
                    familiares=familiares,
                    numero_cot=numero_cot,
                )

            # Validación: al menos un Plan, Servicio o Familiar
            if not (planes_seleccionado or servicios_seleccionados or familiares_seleccionado):
                return render_template(
                    "agregar_cotizacion.html",
                    title="Agregar Cotización",
                    error="Debes seleccionar al menos un Plan, Servicio o Familiar.",
                    planes=planes,
                    servicios=servicios,
                    familiares=familiares,
                    numero_cot=numero_cot,
                )

            # Insertar la cotización principal
            cur.execute(
                """
                INSERT INTO Cotizacion (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot)
                VALUES (?, ?, ?, ?, ?)
            """,
                (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot),
            )
            id_cotizacion = cur.lastrowid

            # Insertar detalle del plan (si existe)
            if planes_seleccionado:
                cur.execute(
                    """
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                    VALUES (?, ?, ?, ?)
                """,
                    (id_cotizacion, int(planes_seleccionado), None, None),
                )

            # Insertar detalle de familiares
            for f_id in set(familiares_seleccionado):
                cur.execute(
                    """
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                    VALUES (?, ?, ?, ?)
                """,
                    (id_cotizacion, None, None, int(f_id)),
                )

            # Insertar detalle de servicios
            for s_id in set(servicios_seleccionados):
                cantidad = request.form.get(f"cantidad_{s_id}", 1)
                cur.execute(
                    """
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar, cantidad)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (id_cotizacion, None, int(s_id), None, int(cantidad)),
                )

            # Commit único al final
            conn.commit()
            return redirect(url_for("cotizacion.listar"))

        return render_template(
            "agregar_cotizacion.html",
            title="Agregar Cotización",
            planes=planes,
            servicios=servicios,
            familiares=familiares,
            numero_cot=numero_cot,
        )


# ----------------------------------------Opcion de descargar PDF ya que es cotizaciones----------------------------------------
@cotizaciones_bd.route("/pdf/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "exportar")
def descargar_pdf(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cur = conn.cursor()

    fecha_actual = date.today()

    # Cotizacion principal :)
    cotizacion = cur.execute(
        """
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()
    if not cotizacion:
        conn.close()
        return "cotizacion no encontrado", 404

    # Obtener el plan asociado
    plan = cur.execute(
        """
        SELECT p.id_plan, p.tipo_plan, p.precio_plan, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
    """,
        (id,),
    ).fetchone()

    # Obtener los servicios asociados
    servicios = cur.execute(
        """
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """,
        (id,),
    ).fetchall()

    # Obtener los familiares asociados
    familiares = cur.execute(
        """
        SELECT DISTINCT f.id_familiar, f.f_nombre, f.f_apellido,f.f_correo
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ? AND cd.id_familiar IS NOT NULL
    """,
        (id,),
    ).fetchall()
    conn.close()

    try:
        rendered_html = render_template(
            "pdf.html",
            cotizacion=cotizacion,
            plan=plan,
            servicios=servicios,
            familiares=familiares,
            fecha_actual=fecha_actual,
        )
        pdf_buffer = io.BytesIO()

        HTML(string=rendered_html, base_url=request.host_url).write_pdf(target=pdf_buffer)

        pdf_byte_string = pdf_buffer.getvalue()
        pdf_buffer.close()

        response = Response(pdf_byte_string, content_type="application/pdf")
        response.headers["Content-Disposition"] = "inline; filename=pdf.pdf"
        return response
    except Exception as e:
        return f"Error al generar el PDF: {str(e)}", 500
