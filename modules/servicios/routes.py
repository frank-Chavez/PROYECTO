from flask import Blueprint,render_template, abort, redirect, url_for
from jinja2 import TemplateNotFound
from database import conection

servicios_bd = Blueprint("servicios", __name__, url_prefix="/servicios", template_folder="templates")



@servicios_bd.route('/')
def listar():
    conn=conection()
    servicios = conn.execute("SELECT * FROM servicios").fetchall()
    conn.close()
    return render_template("servicios.html", servicios=servicios, title="servicios")


@servicios_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    servicios = conn.execute("SELECT estado_serv FROM Servicios WHERE id_servicio = ?", (id,)).fetchone()
    
    if servicios:
        nuevo_estado = 0 if servicios["estado_serv"] == 1 else 1
        conn.execute("UPDATE Servicios SET estado_serv = ? WHERE id_servicio = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('servicios.listar'))