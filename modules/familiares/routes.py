from flask import Blueprint,render_template, redirect, url_for,request
from database import conection


familiares_bd = Blueprint("familiares", __name__, url_prefix="/familiares", template_folder="templates", static_folder="static")

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




@familiares_bd.route('/VerDetalles/<int:id>', methods=['GET'])
def VerDetalles(id):
    conn = conection()
    familiar = conn.execute("""
        SELECT id_familiar, f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, fechaRegistro, f_estado
        FROM Familiares 
        WHERE id_familiar = ?
    """, (id,)).fetchone()
    conn.close()

    if not familiar:
        return "Familiar no encontrado", 404

    return render_template("detalles_familiares.html", familiar=familiar, title="Detalles del Familiar")



@familiares_bd.route('/agregar', methods=["GET", "POST"] ,endpoint='agregar')
def agregar_familiar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        parentesco = request.form["parentesco"]
        telefono = request.form["telefono"]
        correo = request.form["correo"]
        estado = request.form["estado"]
        fechaRegistro = request.form["fechaRegistro"]

        usuario_id = 1  # ajusta según tu lógica de login

        conn = conection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Familiares (
                f_nombre, f_apellido, f_parentesco, f_telefono, f_correo, f_estado, fechaRegistro, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, parentesco, telefono, correo, estado, fechaRegistro, usuario_id))
        conn.commit()
        conn.close()

        # 👇 Aquí el cambio: redirige a la lista de familiares
        return redirect(url_for("familiares.listar"))
    

    return render_template("agregar_familiar.html", title="Familiar")
