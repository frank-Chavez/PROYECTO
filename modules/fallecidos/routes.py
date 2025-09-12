from flask import Blueprint,render_template, abort , redirect, url_for, request
from jinja2 import TemplateNotFound
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