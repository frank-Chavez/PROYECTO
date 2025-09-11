from flask import Blueprint,render_template, abort, redirect, url_for
from jinja2 import TemplateNotFound 
from database import conection

proveedor_bd = Blueprint("proveedor", __name__, url_prefix="/proveedor", template_folder="templates")



@proveedor_bd.route('/')
def listar():
    conn=conection()
    proveedor = conn.execute("SELECT * FROM Proveedores").fetchall()
    conn.close()
    return render_template("proveedor.html", proveedor=proveedor, title="Proveedor")



@proveedor_bd.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Proveedores  WHERE id_proveedor  = ?", (id,))
    conn.commit()
    return redirect(url_for('proveedor.listar'))