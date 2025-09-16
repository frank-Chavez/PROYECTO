from flask import Blueprint,render_template, abort, redirect, url_for, request
from jinja2 import TemplateNotFound
from database import conection

cotizaciones_bd = Blueprint("cotizacion", __name__, url_prefix="/cotizacion", template_folder="templates")



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
            """, (numerocot, fechacot, montocot, validacioncot, estado, id))
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

@cotizaciones_bd.route('/agregar', methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        numero_cot = request.form.get("numero_cot")
        fecha_cot = request.form.get("fecha_cot")
        monto_cot = request.form.get("monto_cot")
        validacion_cot = request.form.get("validacion_cot")
        estado_cot = request.form.get("estado_cot", "Activo")

        # Validaciones simples
        if not (numero_cot and fecha_cot and monto_cot and validacion_cot):
            # Si quieres, podrías usar flash() para mostrar mensajes
            return render_template("agregar_cotizacion.html", title="Agregar Cotización", error="Completa todos los campos.")

        conn = conection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Cotizacion (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot)
            VALUES (?, ?, ?, ?, ?)
        """, (numero_cot, fecha_cot, monto_cot, validacion_cot, estado_cot))
        conn.commit()
        conn.close()

        return redirect(url_for('cotizacion.listar'))

    return render_template("agregar_cotizacion.html", title="Agregar Cotización")
