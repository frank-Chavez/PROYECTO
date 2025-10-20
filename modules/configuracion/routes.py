from flask import Blueprint, render_template, session, redirect, url_for
from database import conection

configuracion_bd = Blueprint(
    "configuracion", __name__, url_prefix="/configuracion", template_folder="templates", static_folder="static"
)


@configuracion_bd.route("/")
def index():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    return render_template(
        "configuracion.html",
    )


@configuracion_bd.route("/usuarios")
def usuarios():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    usuario = conn.execute("SELECT * FROM Usuario").fetchall()
    conn.close()

    return render_template("usuarios.html", usuario=usuario, title="usuarios")


@configuracion_bd.route("/permisos")
def permisos():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    permisos = conn.execute("SELECT * FROM Usuario").fetchall()
    conn.close()

    return render_template("permisos.html", permisos=permisos, title="Permisos")
