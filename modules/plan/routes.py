from flask import Blueprint,render_template, abort, redirect, url_for,request
from jinja2 import TemplateNotFound
from jinja2 import TemplateNotFound
from database import conection

planes_bd = Blueprint("planes", __name__, url_prefix="/planes", template_folder="templates")

@planes_bd.route('/')
def listar():
    conn=conection()
    planes = conn.execute("SELECT * FROM planes").fetchall()
    conn.close()
    return render_template("planes.html", planes=planes, title="planes")



@planes_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    planes = conn.execute("SELECT estado_plan FROM Planes WHERE id_plan = ?", (id,)).fetchone()
    
    if planes:
        nuevo_estado = 0 if planes["estado_plan"] == 1 else 1
        conn.execute("UPDATE Planes SET estado_plan = ? WHERE id_plan = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('planes.listar'))



@planes_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn= conection()

    if request.method == "POST":
        tipoPlan = request.form['tipo_plan']
        precioPlan = request.form['precio_plan']
        duracionPlan = request.form['duracion_plan']
        categoriaPlan = request.form['categoria_plan']
        condicionesPlan = request.form['condiciones_plan']
        estado = request.form['estado_plan']

        conn.execute("""
                UPDATE Planes 
                SET tipo_plan = ?, precio_plan = ?, duracion_plan = ?, categoria_plan = ?, condiciones_plan = ?, estado_plan    = ?
                WHERE id_plan = ?
            """, (tipoPlan, precioPlan, duracionPlan,  categoriaPlan, condicionesPlan, estado, id))
        conn.commit()  
        conn.close()

        return redirect(url_for('planes.listar'))
    
    editar = conn.execute("""
        SELECT id_plan, tipo_plan, precio_plan, duracion_plan, categoria_plan, condiciones_plan, estado_plan  
        FROM Planes 
        WHERE id_plan = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar_plan.html", plan=editar, title="Registrar plan")