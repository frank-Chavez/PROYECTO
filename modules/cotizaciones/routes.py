from flask import Blueprint,render_template, redirect, url_for, request
from database import conection

cotizaciones_bd = Blueprint("cotizacion", __name__, url_prefix="/cotizacion", template_folder="templates", static_folder="static")



@cotizaciones_bd .route('/')
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
    conn= conection()

    if request.method == "POST":
        numerocot = request.form['numero_cot']
        fechacot = request.form['fecha_cot']
        montocot = request.form['monto_cot']
        validacioncot = request.form['validacion_cot']
        estado = request.form['estado_cot']

        conn.execute("""
                UPDATE Cotizacion 
                SET numero_cot = ?, fecha_cot = ?, monto_cot = ?, estado_cot = ?, validacion_cot = ?
                WHERE id_cotizacion = ?
            """, (numerocot, fechacot, montocot, estado, validacioncot,  id))
        conn.commit()  
        conn.close()

        return redirect(url_for('cotizacion.listar'))
    
    editar = conn.execute("""
        SELECT id_cotizacion, numero_cot, fecha_cot, monto_cot, estado_cot, validacion_cot 
        FROM Cotizacion 
        WHERE id_cotizacion = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar_Cotizaciones.html", cot=editar, title="Registrar servico")



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
        SELECT s.id_servicio, s.tipo_serv, s.precio_serv
        FROM cotizacion_detalles cd
        JOIN Servicios s ON cd.id_servicio = s.id_servicio
        WHERE cd.id_cotizacion = ? AND cd.id_servicio IS NOT NULL
    """, (id,)).fetchall()

    # Obtener los familiares asociados
    familiares = cur.execute("""
        SELECT f.id_familiar, f.f_nombre, f.f_apellido
        FROM cotizacion_detalles cd
        JOIN Familiares f ON cd.id_familiar = f.id_familiar
        WHERE cd.id_cotizacion = ? AND cd.id_familiar IS NOT NULL
    """, (id,)).fetchall()

    conn.close()
    return render_template("detalles_cotizaciones.html", cotizacion=cotizacion,plan=plan,servicios=servicios,familiares=familiares, title="Detalles del cotizacion")



@cotizaciones_bd.route('/agregar', methods=["GET", "POST"])
def agregar():
    conn = conection()
    cur = conn.cursor()

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

    # Planes activos
    cur.execute("SELECT id_plan, tipo_plan, precio_plan FROM Planes WHERE estado_plan = '1'")
    planes = cur.fetchall()
    # Servicios activos
    cur.execute("SELECT id_servicio, tipo_serv, precio_serv FROM Servicios WHERE estado_serv = '1'")
    servicios = cur.fetchall()
    # clientes(familiares) activos
    cur.execute("SELECT id_familiar , f_nombre, f_apellido FROM Familiares WHERE f_estado = '1'")
    familiares = cur.fetchall()



    if request.method == "POST":
        fecha_cot = request.form.get("fecha_cot")
        monto_cot = request.form.get("monto_cot")
        validacion_cot = request.form.get("validacion_cot")
        estado_cot = request.form.get("estado_cot", 1)
        planes_seleccionado = request.form.get("plan_cremacion")
        servicios_seleccionado = request.form.getlist("servicio_adicional")
        familiares_seleccionado = request.form.get("nombre_cliente")

        if not (fecha_cot and monto_cot and validacion_cot):
            conn.close()
            return render_template("agregar_cotizacion.html", title="Agregar Cotización", error="Completa todos los campos.", planes=planes, servicios=servicios, familiares=familiares  ,numero_cot=numero_cot)
        
        # Calcular el monto total sumando el monto de planes y servicios seleccionados
        total = 0
        if planes_seleccionado:
            plan_precio = cur.execute("SELECT precio_plan FROM Planes WHERE id_plan = ?", (planes_seleccionado,)).fetchone()
            if plan_precio:
                total += plan_precio['precio_plan']

        if servicios_seleccionado:
            for s_id in servicios_seleccionado:
                precio = cur.execute("SELECT precio_serv FROM Servicios WHERE id_servicio = ?", (s_id,)).fetchone()
                if precio:
                    total += precio['precio_serv']

        
        cur.execute("""
            INSERT INTO Cotizacion (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot)
            VALUES (?, ?, ?, ?, ?)  
        """, (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot))

        id_cotizacion = cur.lastrowid

        # Insertar detalle del plan
        planes_seleccionado = request.form.get("plan_cremacion")

        if planes_seleccionado:  # solo si se seleccionó un Plan
            planes_seleccionado = int(planes_seleccionado)
        cur.execute("""
            INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
            VALUES (?, ?, ?, ?)
        """, (id_cotizacion, planes_seleccionado, None, None))


        # Insertar detalle del servicio
        servicios_seleccionado = request.form.get("servicio_adicional")

        for s_id in servicios_seleccionado:
            cur.execute("""
                INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
                VALUES (?, ?, ?, ?)
            """, (id_cotizacion, None, servicios_seleccionado, None))

        
        # Insertar detalle del cliente (familiar)
        familiares_seleccionado = request.form.get("nombre_cliente")

        if familiares_seleccionado:  # solo si se seleccionó un familiar
            familiares_seleccionado = int(familiares_seleccionado)
        cur.execute("""
            INSERT INTO cotizacion_detalles (id_cotizacion, id_plan, id_servicio, id_familiar)
            VALUES (?, ?, ?, ?)
        """, (id_cotizacion, None, None, familiares_seleccionado))

        conn.commit()
        conn.close()

        return redirect(url_for('cotizacion.listar'))

    conn.close()
    return render_template("agregar_cotizacion.html", title="Agregar Cotización",planes=planes, servicios=servicios, familiares=familiares, numero_cot=numero_cot)

