from flask import Blueprint,render_template, abort, redirect, url_for
from jinja2 import TemplateNotFound
from database import conection

cotizaciones_bd = Blueprint("cotizacion", __name__, url_prefix="/cotizacion", template_folder="templates")



@cotizaciones_bd .route('/cotizacion')
def listar():
    conn=conection()
    cotizacion = conn.execute("SELECT * FROM Cotizacion").fetchall()
    conn.close()
    return render_template("cotizacion.html", cotizacion=cotizacion, title="cotizaciones")


@cotizaciones_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Cotizacion WHERE id_cotizacion = ?", (id,))
    conn.commit()
    return redirect(url_for('cotizacion.listar'))