from flask import Blueprint,render_template, abort, redirect, url_for
from jinja2 import TemplateNotFound
from database import conection

servicios_bd = Blueprint("servicios", __name__, url_prefix="/servicios", template_folder="templates")



@servicios_bd.route('/servicios')
def listar():
    conn=conection()
    servicios = conn.execute("SELECT * FROM servicios").fetchall()
    conn.close()
    return render_template("servicios.html", servicios=servicios, title="servicios")


@servicios_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Servicios  WHERE id_servicio  = ?", (id,))
    conn.commit()
    return redirect(url_for('servicios.listar'))