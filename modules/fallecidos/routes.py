from flask import Blueprint,render_template, abort , redirect, url_for
from jinja2 import TemplateNotFound
from database import conection

fallecidos_bd = Blueprint("fallecidos", __name__, url_prefix="/fallecidos", template_folder="templates")


@fallecidos_bd.route('/')
def listar():
    conn=conection()
    fallecidos = conn.execute("SELECT * FROM Fallecidos").fetchall()
    conn.close()
    return render_template("fallecidos.html", Fallecidos=fallecidos, title="Fallecidos")



@fallecidos_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM fallecidos WHERE id_fallecido = ?", (id,))
    conn.commit()
    return redirect(url_for('fallecidos.listar'))