from flask import Blueprint, render_template, redirect, url_for, request, send_file, session
from database import conection
import pandas as pd
import io


planes_bd = Blueprint("planes", __name__, url_prefix="/planes", template_folder="templates", static_folder="static")


@planes_bd.route("/")
def listar():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    planes = conn.execute("SELECT * FROM planes").fetchall()
    conn.close()
    return render_template("planes.html", planes=planes, title="planes")


@planes_bd.route("/cambiar_estado/<int:id>", methods=["GET"])
def cambiar_estado(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    planes = conn.execute("SELECT estado_plan FROM Planes WHERE id_plan = ?", (id,)).fetchone()

    if planes:
        nuevo_estado = 0 if planes["estado_plan"] == 1 else 1
        conn.execute("UPDATE Planes SET estado_plan = ? WHERE id_plan = ?", (nuevo_estado, id))
        conn.commit()

    conn.close()
    return redirect(url_for("planes.listar"))


@planes_bd.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()

    if request.method == "POST":
        tipoPlan = request.form["tipo_plan"]
        precioPlan = request.form["precio_plan"]
        duracionPlan = request.form["duracion_plan"]
        categoriaPlan = request.form["categoria_plan"]
        condicionesPlan = request.form["condiciones_plan"]
        estado = request.form["estado_plan"]

        conn.execute(
            """
                UPDATE Planes 
                SET tipo_plan = ?, precio_plan = ?, duracion_plan = ?, categoria_plan = ?, condiciones_plan = ?, estado_plan    = ?
                WHERE id_plan = ?
            """,
            (tipoPlan, precioPlan, duracionPlan, categoriaPlan, condicionesPlan, estado, id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("planes.listar"))

    editar = conn.execute(
        """
        SELECT id_plan, tipo_plan, precio_plan, duracion_plan, categoria_plan, condiciones_plan, estado_plan  
        FROM Planes 
        WHERE id_plan = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    return render_template("editar_plan.html", plan=editar, title="Registrar plan")


@planes_bd.route("/VerDetalles/<int:id>", methods=["GET"])
def VerDetalles(id):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conn = conection()
    plan = conn.execute(
        """
        SELECT id_plan, tipo_plan, precio_plan, duracion_plan, categoria_plan, condiciones_plan, estado_plan  
        FROM Planes 
        WHERE id_plan = ?
    """,
        (id,),
    ).fetchone()
    conn.close()

    if not plan:
        return "plan no encontrado", 404

    return render_template("detalles_plan.html", plan=plan, title="Detalles del plan")


@planes_bd.route("/agregar", methods=["GET", "POST"], endpoint="agregar")
def agregar_plan():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo_plan = request.form["tipo_plan"]
        precio_plan = request.form["precio_plan"]
        duracion_plan = request.form["duracion_plan"]
        categoria_plan = request.form["categoria_plan"]
        condiciones_plan = request.form["condiciones_plan"]
        estado_plan = request.form["estado_plan"]

        conn = conection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Planes (tipo_plan, precio_plan, duracion_plan, categoria_plan, condiciones_plan, estado_plan)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (tipo_plan, precio_plan, duracion_plan, categoria_plan, condiciones_plan, estado_plan),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("planes.listar"))

    return render_template("agregar_plan.html", title="Agregar Plan")


@planes_bd.route("/exel")
def exel():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    try:
        # coneccion a la bd
        conn = conection()
        # consultando la informacion que se va a descargar
        consulta = """
        SELECT 
            p.tipo_plan AS 'Tipo del Plan',
            p.precio_plan AS 'Precio del Plan',
            p.duracion_plan AS 'Duracion del Plan',
            p.categoria_plan AS 'Categoria del Plan',
            p.condiciones_plan AS 'Condiciones del Plan',
            p.estado_plan AS 'Estado',
            CASE 
                WHEN p.estado_plan = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Planes p
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Planes")

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="Planes.xlsx",
            as_attachment=True,
        )

    except Exception as e:
        import traceback

        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500
