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