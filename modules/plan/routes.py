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




@planes_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Planes WHERE id_plan = ?", (id,))
    conn.commit()
    return redirect(url_for('planes.listar'))