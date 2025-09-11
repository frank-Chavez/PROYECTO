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



@proveedor_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    proveedor = conn.execute("SELECT estado_p FROM Proveedores WHERE id_proveedor = ?", (id,)).fetchone()
    
    if proveedor:
        nuevo_estado = 0 if proveedor["estado_p"] == 1 else 1
        conn.execute("UPDATE Proveedores SET estado_p = ? WHERE id_proveedor = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('proveedor.listar'))