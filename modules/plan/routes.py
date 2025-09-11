from flask import Blueprint,render_template, abort, redirect, url_for
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