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



@familiares_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    familiares = conn.execute("SELECT f_estado FROM Familiares WHERE id_familiar = ?", (id,)).fetchone()
    
    if familiares:
        nuevo_estado = 0 if familiares["f_estado"] == 1 else 1
        conn.execute("UPDATE Familiares SET f_estado = ? WHERE id_familiar = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('familiares.listar'))