from flask import Blueprint,render_template, redirect, url_for,request
from database import conection


familiares_bd = Blueprint("familiares", __name__, url_prefix="/familiares", template_folder="templates")

@familiares_bd.route("/")
def listar():
    conn = conection()
    familiares = conn.execute("SELECT * FROM Familiares").fetchall()
    conn.close()
    return render_template("familiares.html",  familiares=familiares,  title="Familiares")



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



@familiares_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn= conection()

    if request.method == "POST":
        nombre = request.form['f_nombre']
        apellido = request.form['f_apellido']
        parentesco = request.form['f_parentesco']
        telefono = request.form['f_telefono']
        correo = request.form['f_correo']
        estado = request.form['f_estado']
        fechaRegistro = request.form['fechaRegistro']

        conn.execute("""
                UPDATE Familiares 
                SET f_nombre = ?, f_apellido = ?, f_parentesco = ?, f_telefono = ?, f_correo = ?, f_estado = ?, fechaRegistro = ?
                WHERE id_familiar = ?
            """, (nombre, apellido, parentesco, telefono, correo, estado, fechaRegistro, id))
        conn.commit()  
        conn.close()

        return redirect(url_for('familiares.listar'))
    
    editar = conn.execute("""
        SELECT id_familiar, f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, f_estado, fechaRegistro 
        FROM Familiares 
        WHERE id_familiar = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar.html", familiar=editar)
