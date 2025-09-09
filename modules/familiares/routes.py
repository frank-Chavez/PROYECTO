from flask import Blueprint,render_template, abort, redirect, url_for
from jinja2 import TemplateNotFound
from database import conection


familiares_bd = Blueprint("familiares", __name__, url_prefix="/familiares", template_folder="templates")

@familiares_bd.route("/")
def listar():
    conn = conection()
    familiares = conn.execute("SELECT * FROM Familiares").fetchall()
    conn.close()
    return render_template("familiares.html", familiares=familiares, title="Familiares")



@familiares_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Familiares WHERE id_familiar = ?", (id,))
    conn.commit()
    return redirect(url_for('familiares.listar'))