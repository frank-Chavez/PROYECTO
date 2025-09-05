import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)


# Conexión a la base de datos (función para abrirla)
def conection():
    conn = sqlite3.connect("database.db")  # tu archivo .db
    conn.row_factory = sqlite3.Row  # para acceder a las columnas por nombre
    return conn

@app.route('/', methods=["GET", "POST"])
def login():
    error = None
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")  # 👈 cambia al nombre de tu BD
        cursor = conn.cursor()

        # Verificar usuario y contraseña
        cursor.execute("SELECT id_usuario, nombre_u, rol_id FROM Usuario WHERE LOWER(nombre_u) = LOWER(?) AND contraseña_u = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Si encuentra coincidencia
            return render_template("dashboar.html")
        else:
            # Si no coincide
            error = "❌ Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)



@app.route('/dashboar')
def dashboar():
    return render_template('dashboar.html', title="dashboar")

@app.route('/familiares')
def familiares():
    conn= conection()
    familiares = conn.execute("SELECT * FROM Familiares").fetchall()
    conn.close()
    return render_template("familiares.html", familiares=familiares, title="Familiares")


@app.route('/fallecidos')
def fallecidos():
    conn=conection()
    fallecidos = conn.execute("SELECT * FROM Fallecidos").fetchall()
    conn.close()
    return render_template("Fallecidos.html", Fallecidos=fallecidos, title="Fallecidos")


@app.route('/proveedor')
def proveedor():
    conn=conection()
    proveedor = conn.execute("SELECT * FROM Proveedores").fetchall()
    conn.close()
    return render_template("proveedor.html", proveedor=proveedor, title="Proveedor")

@app.route('/planes')
def planes():
    conn=conection()
    planes = conn.execute("SELECT * FROM planes").fetchall()
    conn.close()
    return render_template("planes.html", planes=planes, title="planes")

@app.route('/servicios')
def servicios():
    conn=conection()
    servicios = conn.execute("SELECT * FROM servicios").fetchall()
    conn.close()
    return render_template("servicios.html", servicios=servicios, title="servicios")

@app.route('/cotizacion')
def cotizacion():
    conn=conection()
    cotizacion = conn.execute("SELECT * FROM cotizacion").fetchall()
    conn.close()
    return render_template("cotizacion.html", cotizacion=cotizacion, title="cotizaciones")


@app.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn=conection()
    conn.execute("DELETE FROM Familiares WHERE id_familiar = ?", (id,))
    conn.commit()
    return redirect(url_for('familiares'))



if __name__ == "__main__":
    app.run(debug=True)















"""
@app.route('/bd')
def index():
    # Ejemplo: leer datos de una tabla llamada "usuarios"
    conn = conection()
    rows = conn.execute("SELECT * FROM usuario").fetchall()
    conn.close()
    return render_template('index.html', usuarios=rows)
"""
"""
@app.route('/add_user', methods=["POST"])
def add_user():
    nombre= request.form["nombre_u"]
    contraseña= request.form["contraseña_u"]
    conn= conection()
    conn.execute("INSERT INTO Usuario (nombre_u, contraseña_u) VALUES (?, ?)",(nombre, contraseña ))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))"""



