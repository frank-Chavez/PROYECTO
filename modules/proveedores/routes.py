from flask import Blueprint,render_template, redirect, url_for, request
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


@proveedor_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn= conection()

    if request.method == "POST":
        nombreProveedor = request.form['nombre_p']
        telefono = request.form['telefono_p']
        correo = request.form['correo_p']
        servicio = request.form['servicio_p']
        fechaRegistro = request.form['fechaRegistro_p']
        estado = request.form['estado_p']

        conn.execute("""
                UPDATE Proveedores 
                SET nombre_p = ?, telefono_p = ?, correo_p = ?, servicio_p = ?, fechaRegistro_p = ?, estado_p    = ?
                WHERE id_proveedor = ?
            """, (nombreProveedor, telefono, correo,  servicio, fechaRegistro, estado, id))
        conn.commit()  
        conn.close()

        return redirect(url_for('proveedor.listar'))
    
    editar = conn.execute("""
        SELECT id_proveedor, nombre_p, telefono_p, correo_p, servicio_p, fechaRegistro_p, estado_p  
        FROM Proveedores 
        WHERE id_proveedor = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar_proveedor.html", Proveedor=editar, title="Registrar proveedor")



@proveedor_bd.route('/agregar', methods=["GET", "POST"] , endpoint='agregar')
def agregar_fallecido():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["Telefono"]
        correo = request.form["correo"]
        servicio = request.form["servicio"]
        fechaRegistro = request.form["fechaRegistro"]
        estado = request.form["estado"]


        conn = conection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Proveedores (
                nombre_p, telefono_p, correo_p, servicio_p, fechaRegistro_p, estado_p
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, telefono, correo, servicio,  fechaRegistro, estado))
        conn.commit()
        conn.close()

        return redirect(url_for("proveedor.listar"))

    return render_template("agregar_proveedor.html", title="Proveedor")