from flask import Flask, render_template, request, redirect, url_for, session
from database import conection
from dotenv import load_dotenv
import os
from modules.familiares.routes import familiares_bd
from modules.fallecidos.routes import fallecidos_bd
from modules.plan.routes import planes_bd
from modules.proveedores.routes import proveedor_bd
from modules.servicios.routes import servicios_bd
from modules.cotizaciones.routes import cotizaciones_bd 



load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


app.register_blueprint(familiares_bd)
app.register_blueprint(fallecidos_bd)
app.register_blueprint(planes_bd)
app.register_blueprint(proveedor_bd)
app.register_blueprint(servicios_bd)
app.register_blueprint(cotizaciones_bd )

if __name__== "__main__":
    cotizaciones_bd.run(debug=True)

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        
        username = request.form["username"]
        password = request.form["password"]

        conn = conection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Usuario WHERE nombre_u=? AND contraseña_u=?", (username, password))
        account = cursor.fetchone()

        if account:
            session['logueado'] = True
            session['id_usuario'] = account['id_usuario']
            session['rol_id'] = account['rol_id']

            if session['rol_id'] == 1:
                return redirect(url_for("dashboar"))
            elif session['rol_id'] == 2:
                return redirect(url_for("dashboar"))
            else:
                return render_template("login.html", mensaje="Rol desconocido.")
        else:
            return render_template("login.html", mensaje="Usuario o Contraseña incorrecta")

    # 🔹 Si llega aquí por GET
    return render_template("login.html")








@app.route("/dashboar", endpoint="dashboar")
def dashboar():
    conn = conection()

    familiares_count = conn.execute("""
        SELECT COUNT(*) AS n
        FROM Familiares
        WHERE LOWER(TRIM(f_estado)) = 'activo' OR TRIM(f_estado) = '1'
    """).fetchone()["n"]

    servicios_count = conn.execute("""
        SELECT COUNT(*) AS n
        FROM Servicios
        WHERE LOWER(TRIM(estado_serv)) = 'activo' OR TRIM(estado_serv) = '1'
    """).fetchone()["n"]

    cotizaciones_count = conn.execute("""
        SELECT COUNT(*) AS n
        FROM Cotizacion
        WHERE LOWER(TRIM(fecha_cot)) = 'activo' OR TRIM(estado_cot) = '1'
    """).fetchone()["n"]

    proveedores_count = conn.execute("""
        SELECT COUNT(*) AS n
        FROM Proveedores
        WHERE LOWER(TRIM(estado_p)) = 'activo' OR TRIM(estado_p) = '1'
    """).fetchone()["n"]

    # === Últimos (igual que ya tenías) ===
    rf = conn.execute("""
        SELECT (COALESCE(f_nombre,'') || ' ' || COALESCE(f_apellido,'')) AS nombre, fechaRegistro
        FROM Familiares
        ORDER BY (fechaRegistro IS NULL), datetime(fechaRegistro) DESC, id_familiar DESC
        LIMIT 1
    """).fetchone()
    reciente_familiar = (rf["nombre"], rf["fechaRegistro"]) if rf else None

    rc = conn.execute("""
        SELECT numero_cot, fecha_cot
        FROM Cotizacion
        ORDER BY datetime(fecha_cot) DESC, id_cotizacion DESC
        LIMIT 1
    """).fetchone()
    reciente_cotizacion = (rc["numero_cot"], rc["fecha_cot"]) if rc else None

    rs = conn.execute("""
        SELECT tipo_serv, estado_serv
        FROM Servicios
        ORDER BY id_servicio DESC
        LIMIT 1
    """).fetchone()
    reciente_servicio = (rs["tipo_serv"], rs["estado_serv"]) if rs else None

    rp = conn.execute("""
        SELECT nombre_p, fechaRegistro_p
        FROM Proveedores
        ORDER BY datetime(fechaRegistro_p) DESC, id_proveedor DESC
        LIMIT 1
    """).fetchone()
    reciente_proveedor = (rp["nombre_p"], rp["fechaRegistro_p"]) if rp else None

    conn.close()

    return render_template(
        "dashboar.html",
        familiares_count=familiares_count,
        servicios_count=servicios_count,
        cotizaciones_count=cotizaciones_count,
        proveedores_count=proveedores_count,
        reciente_familiar=reciente_familiar,
        reciente_cotizacion=reciente_cotizacion,
        reciente_servicio=reciente_servicio,
        reciente_proveedor=reciente_proveedor,
        title="Dashboar"
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



