from flask import (
    Response,
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
)
import urllib.parse
from database import conection
from decoradores import permiso_requerido
from datetime import date
import io
import base64
from weasyprint import HTML

cotizaciones_bd = Blueprint(
    "cotizaciones", __name__, url_prefix="/cotizacion", template_folder="templates", static_folder="static"
)


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

    # Consulta directa sin JOIN (ahora usamos nombre_cliente)
    cursor.execute(
        """
        SELECT
            id_cotizacion,
            numero_cot,
            fecha_cot,
            monto_cot,
            validacion_cot,
            estado_cot,
            nombre_cliente
        FROM Cotizacion
        ORDER BY id_cotizacion DESC
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
                id_cotizacion,
                numero_cot,
                fecha_cot,
                monto_cot,
                validacion_cot,
                estado_cot,
                nombre_cliente
            FROM Cotizacion
            WHERE LOWER(remove_acentos(nombre_cliente)) LIKE ?
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
    return redirect(url_for("cotizaciones.listar"))


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
    return redirect(url_for("cotizaciones.listar"))


# ----------------------------------------Opcion de editar----------------------------------------
@cotizaciones_bd.route("/editar/<int:id>", methods=["GET", "POST"])
@permiso_requerido("cotizacion", "editar")
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        numerocot = request.form["numero_cot"]
        montocot = request.form["monto_cot"]
        nombre_cliente = request.form.get("nombre_cliente")
        plan_seleccionado = request.form.get("plan_cremacion")
        servicios_seleccionadoss = request.form.getlist("servicios_adicionales")

        conn.execute(
            """
            UPDATE Cotizacion 
            SET numero_cot = ?, monto_cot = ?, nombre_cliente = ?
            WHERE id_cotizacion = ?
        """,
            (numerocot, montocot, nombre_cliente, id),
        )

        conn.execute("DELETE FROM cotizacion_detalles WHERE id_cotizacion = ?", (id,))

        if plan_seleccionado:
            conn.execute(
                """
                INSERT INTO cotizacion_detalles (id_cotizacion, id_plan)
                VALUES (?, ?)
            """,
                (id, int(plan_seleccionado)),
            )

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
        return redirect(url_for("cotizaciones.listar"))

    cotizacion = conn.execute(
        """
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot, nombre_cliente
        FROM Cotizacion WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()

    plan = conn.execute(
        """
        SELECT p.id_plan, p.tipo_plan, precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ?
    """,
        (id,),
    ).fetchone()

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

    familiares = conn.execute(
        """
        SELECT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ?
    """,
        (id,),
    ).fetchall()

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

    cotizacion = cur.execute(
        """
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot, nombre_cliente
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()
    if not cotizacion:
        conn.close()
        return "cotizacion no encontrado", 404

    plan = cur.execute(
        """
        SELECT p.id_plan, p.tipo_plan, p.precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
    """,
        (id,),
    ).fetchone()

    servicios = cur.execute(
        """
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """,
        (id,),
    ).fetchall()

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

        cur.execute("SELECT id_plan, tipo_plan, precio_plan FROM Planes WHERE estado_plan = '1'")
        planes = cur.fetchall()
        cur.execute("SELECT id_servicio, tipo_serv, precio_serv FROM Servicios WHERE estado_serv = '1'")
        servicios = cur.fetchall()
        cur.execute(
            "SELECT id_familiar, f_nombre, f_apellido, f_correo, f_telefono FROM Familiares WHERE f_estado = '1'"
        )
        familiares = cur.fetchall()

        if request.method == "POST":
            fecha_cot = request.form.get("fecha_cot")
            monto_cot = request.form.get("monto_cot")
            nombre_cliente = request.form.get("nombre_cliente")
            cliente_correo = request.form.get("cliente_correo", "").strip() or None

            # Combinar código de país con teléfono
            codigo_pais = request.form.get("codigo_pais", "+51").strip()
            telefono_numero = request.form.get("cliente_telefono", "").strip()
            cliente_telefono = f"{codigo_pais}{telefono_numero}" if telefono_numero else None

            validacion_cot = "Aprobada"
            estado_cot = 1
            plan_seleccionado = request.form.get("plan_cremacion")
            servicios_seleccionados = request.form.getlist("servicios_adicionales")

            if not monto_cot or not nombre_cliente:
                return render_template(
                    "agregar_cotizacion.html",
                    title="Agregar Cotización",
                    error="Completa todos los campos obligatorios.",
                    planes=planes,
                    servicios=servicios,
                    familiares=familiares,
                    numero_cot=numero_cot,
                )

            if not (plan_seleccionado or servicios_seleccionados):
                return render_template(
                    "agregar_cotizacion.html",
                    title="Agregar Cotización",
                    error="Debes seleccionar al menos un Plan o Servicio.",
                    planes=planes,
                    servicios=servicios,
                    familiares=familiares,
                    numero_cot=numero_cot,
                )

            cur.execute(
                """
                INSERT INTO Cotizacion (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot, nombre_cliente, cliente_correo, cliente_telefono)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    numero_cot,
                    fecha_cot,
                    monto_cot,
                    validacion_cot,
                    estado_cot,
                    nombre_cliente,
                    cliente_correo,
                    cliente_telefono,
                ),
            )
            id_cotizacion = cur.lastrowid

            if plan_seleccionado:
                cur.execute(
                    """
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                    VALUES (?, ?, ?, ?)
                """,
                    (id_cotizacion, int(plan_seleccionado), None, None),
                )

            for s_id in set(servicios_seleccionados):
                cantidad = request.form.get(f"cantidad_{s_id}", 1)
                cur.execute(
                    """
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar, cantidad)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (id_cotizacion, None, int(s_id), None, int(cantidad)),
                )

            conn.commit()
            return redirect(url_for("cotizaciones.listar"))

        return render_template(
            "agregar_cotizacion.html",
            title="Agregar Cotización",
            planes=planes,
            servicios=servicios,
            familiares=familiares,
            numero_cot=numero_cot,
        )


# ----------------------------------------Opcion de descargar PDF----------------------------------------
def obtener_pdf_cotizacion(id):
    conn = conection()
    cur = conn.cursor()
    fecha_actual = date.today()

    cotizacion = cur.execute(
        """
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, 
               validacion_cot, estado_cot, nombre_cliente, cliente_correo
        FROM Cotizacion 
        WHERE id_cotizacion = ?
        """,
        (id,),
    ).fetchone()

    if not cotizacion:
        conn.close()
        return None, None

    plan = cur.execute(
        """
        SELECT p.id_plan, p.tipo_plan, p.precio_plan, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
        """,
        (id,),
    ).fetchone()

    servicios = cur.execute(
        """
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
        """,
        (id,),
    ).fetchall()

    result = cur.execute(
        """
        SELECT 
            f.f_nombre,
            f.f_apellido,
            f.f_correo
        FROM cotizacion_detalles cd
        LEFT JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ?
        LIMIT 1
        """,
        (id,),
    ).fetchone()

    cliente = None
    nombre = cotizacion["nombre_cliente"]
    correo = cotizacion["cliente_correo"]

    if not correo and result and result["f_correo"]:
        correo = result["f_correo"]

    if nombre and not correo:
        familiar_encontrado = cur.execute(
            "SELECT f_correo FROM Familiares WHERE (f_nombre || ' ' || f_apellido) = ?", (nombre,)
        ).fetchone()

        if familiar_encontrado:
            correo = familiar_encontrado["f_correo"]

    if nombre:
        cliente = {"nombre": nombre, "correo": correo}
    elif result:
        cliente = {"nombre": f"{result['f_nombre']} {result['f_apellido']}", "correo": result["f_correo"]}

    conn.close()

    rendered_html = render_template(
        "pdf.html", cotizacion=cotizacion, plan=plan, servicios=servicios, cliente=cliente, fecha_actual=fecha_actual
    )

    pdf_buffer = io.BytesIO()
    HTML(string=rendered_html, base_url=request.host_url).write_pdf(target=pdf_buffer)
    return pdf_buffer, cliente


# ----------------------------------------Opcion de descargar PDF----------------------------------------
@cotizaciones_bd.route("/pdf/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "exportar")
def descargar_pdf(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    try:
        pdf_buffer, _ = obtener_pdf_cotizacion(id)

        if not pdf_buffer:
            return "Cotización no encontrada", 404

        response = Response(pdf_buffer.getvalue(), content_type="application/pdf")
        response.headers["Content-Disposition"] = "inline; filename=cotizacion.pdf"

        return response

    except Exception as e:
        return f"Error al generar el PDF: {str(e)}", 500


## ----------------------------------------Opcion de enviar por WhatsApp----------------------------------------
@cotizaciones_bd.route("/whatsapp/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "exportar")
def enviar_whatsapp(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cur = conn.cursor()

    cotizacion = cur.execute(
        """
        SELECT c.id_cotizacion, c.numero_cot, c.nombre_cliente, c.cliente_telefono
        FROM Cotizacion c
        WHERE c.id_cotizacion = ?
        """,
        (id,),
    ).fetchone()

    if not cotizacion:
        conn.close()
        return "Cotización no encontrada", 404

    nombre_cliente = cotizacion["nombre_cliente"]
    telefono = cotizacion["cliente_telefono"]
    nombre_para_mensaje = nombre_cliente

    if not telefono and nombre_cliente:
        familiar_por_nombre = cur.execute(
            """
            SELECT f_telefono, f_nombre 
            FROM Familiares 
            WHERE (f_nombre || ' ' || f_apellido) = ?
            """,
            (nombre_cliente,),
        ).fetchone()

        if familiar_por_nombre and familiar_por_nombre["f_telefono"]:
            telefono = familiar_por_nombre["f_telefono"]
            nombre_para_mensaje = familiar_por_nombre["f_nombre"]

    if not telefono:
        familiar_por_id = cur.execute(
            """
            SELECT 
                f.f_nombre,
                f.f_telefono
            FROM cotizacion_detalles cd
            JOIN Familiares f ON cd.id_familiar = f.id_familiar
            WHERE cd.id_cotizacion = ?
            LIMIT 1
            """,
            (id,),
        ).fetchone()

        if familiar_por_id and familiar_por_id["f_telefono"]:
            telefono = familiar_por_id["f_telefono"]
            nombre_para_mensaje = familiar_por_id["f_nombre"]

    conn.close()

    if not telefono:
        return (
            f"No se encontró un número de teléfono para el cliente '{nombre_cliente}'. Por favor, asegúrate de que el cliente esté registrado en Familiares con un número válido o ingresa el teléfono manualmente.",
            404,
        )

    mensaje = f"Hola {nombre_para_mensaje}, te enviamos los detalles de su cotización."

    whatsapp_url = f"https://api.whatsapp.com/send?phone={telefono}&text={urllib.parse.quote(mensaje)}"
    return redirect(whatsapp_url)


@cotizaciones_bd.route("/email/<int:id>", methods=["GET"])
@permiso_requerido("cotizacion", "exportar")
def enviar_email(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    cur = conn.cursor()

    cotizacion = cur.execute(
        """
        SELECT numero_cot, nombre_cliente, cliente_correo, monto_cot
        FROM Cotizacion WHERE id_cotizacion = ?
    """,
        (id,),
    ).fetchone()

    if not cotizacion:
        conn.close()
        return "Cotización no encontrada", 404

    correo = cotizacion["cliente_correo"] or ""
    nombre_cliente = cotizacion["nombre_cliente"]
    numero_cot = cotizacion["numero_cot"]
    monto = cotizacion["monto_cot"]

    # Buscar correo en familiares si no tiene
    if not correo:
        familiar = cur.execute(
            """
            SELECT f_correo FROM Familiares 
            WHERE TRIM(LOWER(f_nombre || ' ' || f_apellido)) = LOWER(?)
        """,
            (nombre_cliente.strip(),),
        ).fetchone()
        if familiar and familiar["f_correo"]:
            correo = familiar["f_correo"]

    conn.close()
    if not correo:
        return f"No se encontró correo para {nombre_cliente}", 404

    # Generamos solo para tener el nombre del archivo y el saludo
    pdf_buffer, cliente_info = obtener_pdf_cotizacion(id)
    nombre_saludo = cliente_info["nombre"] if cliente_info else nombre_cliente

    asunto = f"Cotización {numero_cot} - Servicios Funerarios"
    cuerpo = f"""Hola {nombre_saludo}.

Muchas gracias por confiar en nosotros.

Te enviamos la cotización solicitada:

• Monto total: S/ {monto:,}

Quedamos a tu disposición para cualquier consulta o para coordinar los siguientes pasos.

Con cariño y respeto,
Crematorio Virgen de la Natividad
WhatsApp: +51 931 112 364 
https://crematoriovirgendelanatividadtpp.com/"""

    # ← URL corta y 100 % segura (nunca dará 400)
    gmail_url = (
        "https://mail.google.com/mail/u/0/?view=cm&fs=1"
        f"&to={urllib.parse.quote(correo)}"
        f"&su={urllib.parse.quote(asunto)}"
        f"&body={urllib.parse.quote(cuerpo)}"
    )

    return redirect(gmail_url)
