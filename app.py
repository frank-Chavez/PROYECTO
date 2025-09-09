from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import conection
from modules.familiares.routes import familiares_bd
from modules.fallecidos.routes import fallecidos_bd
from modules.plan.routes import planes_bd
from modules.proveedores.routes import proveedor_bd
from modules.servicios.routes import servicios_bd
from modules.cotizaciones.routes import cotizaciones_bd 




app = Flask(__name__)

app.register_blueprint(familiares_bd)
app.register_blueprint(fallecidos_bd)
app.register_blueprint(planes_bd)
app.register_blueprint(proveedor_bd)
app.register_blueprint(servicios_bd)
app.register_blueprint(cotizaciones_bd )




@app.route('/', methods=["GET", "POST"])
def login():
    error = None
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = conection() # 👈 cambia al nombre de tu BD
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



