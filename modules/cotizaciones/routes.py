from flask import Blueprint,render_template, abort
from jinja2 import TemplateNotFound
from database import conection

cotizaciones_bd = Blueprint("cotizacion", __name__, url_prefix="/cotizacion", template_folder="templates")



@cotizaciones_bd .route('/cotizacion')
def listar():
    conn=conection()
    cotizacion = conn.execute("SELECT * FROM cotizacion").fetchall()
    conn.close()
    return render_template("cotizacion.html", cotizacion=cotizacion, title="cotizaciones")