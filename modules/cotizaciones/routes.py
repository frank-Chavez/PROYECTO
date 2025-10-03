from flask import Response, request, Blueprint,render_template, redirect, url_for, request
from database import conection
from weasyprint import HTML
import io
from datetime import date

cotizaciones_bd = Blueprint("cotizacion", __name__, url_prefix="/cotizacion", template_folder="templates", static_folder="static")


@cotizaciones_bd.route('/')
def listar():
    conn=conection()
    cotizacion = conn.execute("SELECT * FROM Cotizacion").fetchall()
    conn.close()
    return render_template("cotizacion.html", cotizacion=cotizacion, title="cotizaciones")


@cotizaciones_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    cotizaciones = conn.execute("SELECT estado_cot FROM Cotizacion WHERE id_cotizacion = ?", (id,)).fetchone()
    
    if cotizaciones:
        nuevo_estado = 0 if cotizaciones["estado_cot"] == 1 else 1
        conn.execute("UPDATE Cotizacion SET estado_cot = ? WHERE id_cotizacion = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('cotizacion.listar'))



@cotizaciones_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn = conection()

    if request.method == "POST":
        numerocot = request.form['numero_cot']
        fechacot = request.form['fecha_cot']
        montocot = request.form['monto_cot']
        validacioncot = request.form['validacion_cot']
        estado = request.form['estado_cot']
        plan_seleccionado = request.form.get("plan_cremacion")
        servicios_seleccionadoss = request.form.getlist("servicios_adicionales")
        familiares_seleccionados = request.form.getlist("nombre_cliente")

        # Actualizar cotizacion principal (ahora con el orden correcto)
        conn.execute("""
            UPDATE Cotizacion 
            SET numero_cot = ?, fecha_cot = ?, monto_cot = ?, validacion_cot = ?, estado_cot = ?
            WHERE id_cotizacion = ?
        """, (numerocot, fechacot, montocot, validacioncot, estado, id))

        # Primero eliminamos los detalles antiguos
        conn.execute("DELETE FROM cotizacion_detalles WHERE id_cotizacion = ?", (id,))

        # Insertamos el plan seleccionado
        if plan_seleccionado:
            conn.execute("""
                INSERT INTO cotizacion_detalles (id_cotizacion, id_plan)
                VALUES (?, ?)
            """, (id, int(plan_seleccionado)))

        # Insertamos familiares seleccionados
        for f_id in familiares_seleccionados:
            conn.execute("""
                INSERT INTO cotizacion_detalles (id_cotizacion, id_familiar)
                VALUES (?, ?)
            """, (id, int(f_id)))

        # Insertamos servicios seleccionados (ahora con cantidad)
        for s_id in servicios_seleccionadoss:
            cantidad = request.form.get(f"cantidad_servicio[{s_id}]", 1)
            conn.execute("""
                INSERT INTO cotizacion_detalles (id_cotizacion, id_servicio, cantidad)
                VALUES (?, ?, ?)
            """, (id, int(s_id), int(cantidad)))

        conn.commit()
        conn.close()
        return redirect(url_for('cotizacion.listar'))

    # GET: Traemos cotizacion principal
    cotizacion = conn.execute("""
        SELECT * FROM Cotizacion WHERE id_cotizacion = ?
    """, (id,)).fetchone()

    # Traemos plan asociado
    plan = conn.execute("""
        SELECT p.id_plan, p.tipo_plan, precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ?
    """, (id,)).fetchone()

    # Traemos servicios asociados
    servicios = conn.execute("""
        SELECT s.id_servicio, s.tipo_serv, precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ?
    """, (id,)).fetchall()

    servicios_cantidades = {s["id_servicio"]: s["cantidad"] for s in servicios}

    # Traemos familiares asociados
    familiares = conn.execute("""
        SELECT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ?
    """, (id,)).fetchall()

    # Traemos todas las opciones para mostrar en el form
    planes_disponibles = conn.execute("SELECT id_plan, tipo_plan, precio_plan FROM Planes WHERE estado_plan=1").fetchall()
    servicios_disponibles = conn.execute("SELECT id_servicio, tipo_serv, precio_serv FROM Servicios WHERE estado_serv=1").fetchall()
    familiares_disponibles = conn.execute("SELECT id_familiar, f_nombre, f_apellido FROM Familiares WHERE f_estado=1").fetchall()

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
        title="Editar Cotización"
    )




@cotizaciones_bd.route('/VerDetalles/<int:id>', methods=['GET'])
def VerDetalles(id):
    conn = conection()
    cur = conn.cursor()

    # Cotizacion principal :)
    cotizacion = cur.execute("""
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """, (id,)).fetchone()
    if not cotizacion:
        conn.close()
        return "cotizacion no encontrado", 404
    
    # Obtener el plan asociado
    plan = cur.execute("""
        SELECT p.id_plan, p.tipo_plan, p.precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
    """, (id,)).fetchone()

    # Obtener los servicios asociados
    servicios = cur.execute("""
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv, cd.cantidad
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """, (id,)).fetchall()


    # Obtener los familiares asociados
    familiares = cur.execute("""
        SELECT DISTINCT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ? AND cd.id_familiar IS NOT NULL
    """, (id,)).fetchall()



    conn.close()
    return render_template("detalles_cotizaciones.html", cotizacion=cotizacion, plan=plan, servicios=servicios, familiares=familiares, title="Detalles del cotizacion")




@cotizaciones_bd.route('/agregar', methods=["GET", "POST"])
def agregar():
    with conection() as conn:
        cur = conn.cursor()

        # Obtener último número de cotización
        ultimo = cur.execute("SELECT numero_cot FROM Cotizacion ORDER BY id_cotizacion DESC LIMIT 1").fetchone()
        if ultimo and ultimo["numero_cot"]:
            try:
                numero = int(ultimo["numero_cot"].split('-')[1])
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
            validacion_cot = request.form.get("validacion_cot")
            estado_cot = request.form.get("estado_cot", 1)
            planes_seleccionado = request.form.get("plan_cremacion")
            servicios_seleccionados = request.form.getlist("servicio_adicional")
            familiares_seleccionado = request.form.getlist("nombre_cliente")

            # Validación: campos obligatorios
            if not (fecha_cot and monto_cot and validacion_cot):
                return render_template(
                    "agregar_cotizacion.html",
                    title="Agregar Cotización",
                    error="Completa todos los campos.",
                    planes=planes,
                    servicios=servicios,
                    familiares=familiares,
                    numero_cot=numero_cot
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
                    numero_cot=numero_cot
                )
            

            # Insertar la cotización principal
            cur.execute("""
                INSERT INTO Cotizacion (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot)
                VALUES (?, ?, ?, ?, ?)
            """, (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot))
            id_cotizacion = cur.lastrowid

            # Insertar detalle del plan (si existe)
            if planes_seleccionado:
                cur.execute("""
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                    VALUES (?, ?, ?, ?)
                """, (id_cotizacion, int(planes_seleccionado), None, None))

            # Insertar detalle de familiares
            for f_id in set(familiares_seleccionado): 
                cur.execute("""
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                    VALUES (?, ?, ?, ?)
                """, (id_cotizacion, None, None, int(f_id)))

            # Insertar detalle de servicios
            for s_id in set(servicios_seleccionados): 
                cantidad = request.form.get(f"cantidad_{s_id}",1)
                cur.execute("""
                    INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar, cantidad)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_cotizacion, None, int(s_id), None, int(cantidad)))

            # Commit único al final
            conn.commit()
            return redirect(url_for('cotizacion.listar'))

        return render_template(
            "agregar_cotizacion.html",
            title="Agregar Cotización",
            planes=planes,
            servicios=servicios,
            familiares=familiares,
            numero_cot=numero_cot
        )





@cotizaciones_bd.route('/pdf/<int:id>', methods=["GET"])
def descargar_pdf(id):
    conn = conection()
    cur = conn.cursor()

    fecha_actual = date.today()


    # Cotizacion principal :)
    cotizacion = cur.execute("""
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """, (id,)).fetchone()
    if not cotizacion:
        conn.close()
        return "cotizacion no encontrado", 404
    
    # Obtener el plan asociado
    plan = cur.execute("""
        SELECT p.id_plan, p.tipo_plan, p.precio_plan
        FROM cotizacion_detalles cd
        JOIN Planes p ON cd.id_plan = p.id_plan
        WHERE cd.id_cotizacion = ? AND cd.id_plan IS NOT NULL
    """, (id,)).fetchone()

    # Obtener los servicios asociados
    servicios = cur.execute("""
        SELECT DISTINCT s.id_servicio, s.tipo_serv, s.precio_serv
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """, (id,)).fetchall()


    # Obtener los familiares asociados
    familiares = cur.execute("""
        SELECT DISTINCT f.id_familiar, f.f_nombre, f.f_apellido,f.f_correo
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ? AND cd.id_familiar IS NOT NULL
    """, (id,)).fetchall()
    conn.close()
    
    try:
        rendered_html = render_template("pdf.html", cotizacion=cotizacion, plan=plan, servicios=servicios,familiares=familiares, fecha_actual=fecha_actual)
        pdf_buffer = io.BytesIO()

        HTML(string=rendered_html, base_url=request.host_url).write_pdf(target=pdf_buffer)

        pdf_byte_string = pdf_buffer.getvalue()
        pdf_buffer.close()

        response = Response(pdf_byte_string, content_type="application/pdf")
        response.headers["Content-Disposition"] = "inline; filename=pdf.pdf"
        return response
    except Exception as e:
        return f"Error al generar el PDF: {str(e)}", 500
    