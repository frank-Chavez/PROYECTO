from flask import Blueprint,render_template, redirect, url_for, request
from database import conection

fallecidos_bd = Blueprint("fallecidos", __name__, url_prefix="/fallecidos", template_folder="templates")


@fallecidos_bd.route('/')
def listar():
    conn=conection()
    fallecidos = conn.execute("SELECT * FROM Fallecidos").fetchall()
    conn.close()
    return render_template("fallecidos.html", Fallecidos=fallecidos, title="Fallecidos")



@fallecidos_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    fallecido = conn.execute("SELECT estado_f FROM Fallecidos WHERE id_fallecido = ?", (id,)).fetchone()
    
    if fallecido:
        nuevo_estado = 0 if fallecido["estado_f"] == 1 else 1
        conn.execute("UPDATE Fallecidos SET estado_f = ? WHERE id_fallecido = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('fallecidos.listar'))



@fallecidos_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn= conection()

    if request.method == "POST":
        nombre = request.form['nombre_f']
        edad = request.form['edad_f']
        fechaDefuncion = request.form['fecha_defuncion']
        fechaRegistro = request.form['fechaRegistro_f']
        fechaActualizacion = request.form['fechaActualizacion_f']
        estado = request.form['estado_f']

        conn.execute("""
                UPDATE Fallecidos 
                SET nombre_f = ?, edad_f = ?, fecha_defuncion = ?, fechaRegistro_f = ?, fechaActualizacion_f = ?, estado_f = ?
                WHERE id_fallecido = ?
            """, (nombre, edad, fechaDefuncion,  fechaRegistro, fechaActualizacion, estado, id))
        conn.commit()  
        conn.close()

        return redirect(url_for('fallecidos.listar'))
    
    editar = conn.execute("""
        SELECT id_fallecido, nombre_f, edad_f, fecha_defuncion, fechaRegistro_f, fechaActualizacion_f, estado_f
        FROM Fallecidos 
        WHERE id_fallecido = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar_fallecido.html", fallecidos=editar, title="Registrar Fallecido")


@fallecidos_bd.route('/agregar', methods=["GET", "POST"] , endpoint='agregar')
def agregar_fallecido():
    if request.method == "POST":
        nombre = request.form["nombre"]
        fechaDefuncion = request.form["fechaDefuncion"]
        estado = request.form["estado"]
        edad = request.form["edad"]
        estado = request.form["estado"]
        fechaRegistro = request.form["fechaRegistro"]


        conn = conection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Fallecidos (
                nombre_f, fecha_defuncion, estado_f, edad_f, fechaRegistro_f
            ) VALUES (?, ?, ?, ?, ?)
        """, (nombre, fechaDefuncion, estado, edad,  fechaRegistro))
        conn.commit()
        conn.close()

        return redirect(url_for("fallecidos.listar"))

    return render_template("agregar_fallecido.html", title="Fallecido")





#eliminar
"""@fallecidos_bd.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    conn = conection()
    conn.execute("DELETE FROM Fallecidos WHERE id_fallecido = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("fallecidos.listar"))


<form action="{{ url_for('fallecidos.eliminar', id=f.id_fallecido) }}" method="POST" style="display:inline;">
    <button type="submit" onclick="return confirm('¿Seguro que deseas eliminar este registro?');">
        Eliminar
    </button>
</form>"""