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


@app.route('/dashboard')
def dashboar():
    conn = conection()
    cursor = conn.cursor()

    # --- Contadores ---
    cursor.execute("SELECT COUNT(*) FROM Familiares")
    familiares_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Servicios")
    servicios_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Cotizacion")
    cotizaciones_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Proveedores")
    proveedores_count = cursor.fetchone()[0]

    # --- Actividad reciente (últimos 5 registros por tabla) ---
    cursor.execute("SELECT f_nombre, fechaRegistro FROM Familiares ORDER BY fechaRegistro DESC LIMIT 5")
    recientes_familiares = cursor.fetchall()

    cursor.execute("SELECT numero_cot, fecha_cot FROM Cotizacion ORDER BY fecha_cot DESC LIMIT 5")
    recientes_cotizaciones = cursor.fetchall()

    cursor.execute("SELECT tipo_serv, estado_serv FROM Servicios ORDER BY id_servicio DESC LIMIT 5")
    recientes_servicios = cursor.fetchall()

    cursor.execute("SELECT nombre_p, fechaRegistro_p FROM Proveedores ORDER BY fechaRegistro_p DESC LIMIT 5")
    recientes_proveedores = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboar.html",
        title="Dashboard",
        familiares_count=familiares_count,
        servicios_count=servicios_count,
        cotizaciones_count=cotizaciones_count,
        proveedores_count=proveedores_count,
        recientes_familiares=recientes_familiares,
        recientes_cotizaciones=recientes_cotizaciones,
        recientes_servicios=recientes_servicios,
        recientes_proveedores=recientes_proveedores
    )



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



