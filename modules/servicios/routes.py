from flask import Blueprint, render_template, redirect, url_for, request, send_file
from database import conection
import pandas as pd
import io

servicios_bd = Blueprint("servicios", __name__, url_prefix="/servicios", template_folder="templates", static_folder="static")



@servicios_bd.route('/')
def listar():
    conn=conection()
    servicios = conn.execute("""
    SELECT s.id_servicio,
           s.tipo_serv,
           s.descripcion_serv,
           s.categoria_serv,
           s.precio_serv,
           p.nombre_p ,
           s.estado_serv
    FROM Servicios s
    JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
""").fetchall()
    conn.close()
    return render_template("servicios.html", servicios=servicios, title="Servicios")


@servicios_bd.route('/cambiar_estado/<int:id>', methods=['GET'])
def cambiar_estado(id):
    conn = conection()
    servicios = conn.execute("SELECT estado_serv FROM Servicios WHERE id_servicio = ?", (id,)).fetchone()
    
    if servicios:
        nuevo_estado = 0 if servicios["estado_serv"] == 1 else 1
        conn.execute("UPDATE Servicios SET estado_serv = ? WHERE id_servicio = ?", (nuevo_estado, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('servicios.listar'))


@servicios_bd.route('/editar/<int:id>', methods=['GET','POST'])
def editar(id):
    conn= conection()

    if request.method == "POST":
        tipoServvicio = request.form['tipo_serv']
        descripcion = request.form['descripcion_serv']
        categoria = request.form['categoria_serv']
        servicio = request.form['precio_serv']
        proveedor = request.form['proveedor_id']
        estado = request.form['estado_serv']

        conn.execute("""
                UPDATE Servicios 
                SET tipo_serv = ?, descripcion_serv = ?, categoria_serv = ?, precio_serv = ?, proveedor_id = ?, estado_serv    = ?
                WHERE id_servicio = ?
            """, (tipoServvicio, descripcion, categoria,  servicio, proveedor, estado, id))
        conn.commit()  
        conn.close()

        return redirect(url_for('servicios.listar'))
    
    editar = conn.execute("""
        SELECT id_servicio, tipo_serv, descripcion_serv, categoria_serv, precio_serv, proveedor_id, estado_serv  
        FROM Servicios 
        WHERE id_servicio = ?
    """, (id,)).fetchone()
    conn.close()

    return render_template("editar_servicios.html", servicioss=editar, title="Registrar servico")


@servicios_bd.route('/VerDetalles/<int:id>', methods=['GET'])
def VerDetalles(id):
    conn = conection()
    servicio = conn.execute("""
        SELECT s.id_servicio,
               s.tipo_serv,
               s.descripcion_serv,
               s.categoria_serv,
               s.precio_serv,
               p.nombre_p,
               s.estado_serv
        FROM Servicios s
        JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
        WHERE s.id_servicio = ?
    """, (id,)).fetchone()
    conn.close()

    if not servicio:
        return "Servicio no encontrado", 404

    return render_template("detalles_servicio.html", servicio=servicio, title="Detalles del Servicio")





@servicios_bd.route('/agregar', methods=["GET", "POST"] , endpoint='agregar')
def agregar_fallecido():
    if request.method == "POST":
        tipoServ = request.form["tipoServ"]
        descripcionServ = request.form["descripcionServ"]
        categoriaServ = request.form["categoriaServ"]
        precio_serv = request.form["precio_serv"]
        estado = request.form["estado"]


        conn = conection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Servicios (
                tipo_serv, descripcion_serv, categoria_serv, precio_serv, estado_serv
            ) VALUES (?, ?, ?, ?, ?)
        """, (tipoServ, descripcionServ, categoriaServ, precio_serv,  estado))
        conn.commit()
        conn.close()

        return redirect(url_for("servicios.listar"))

    return render_template("agregar_servicio.html", title="Servicio")




@servicios_bd.route('/exel')
def exel():
    try:
        # coneccion a la bd
        conn = conection()
        #consultando la informacion que se va a descargar
        consulta = """
        SELECT 
            s.tipo_serv AS 'Tipo de servicio',
            s.descripcion_serv AS 'Descripción',
            s.categoria_serv AS 'Categoría',
            s.precio_serv AS 'Precio (S/)',
            p.nombre_p AS 'Proveedor',
            CASE 
                WHEN s.estado_serv = 1 THEN 'Activo'
                ELSE 'Inactivo'
            END AS 'Estado'
        FROM Servicios s
        LEFT JOIN Proveedores p ON s.proveedor_id = p.id_proveedor
        """

        df = pd.read_sql_query(consulta, conn)
        conn.close()

        # se crea el archivo exel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Servicios')

        output.seek(0)

        # Envia el archivo como descarga
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name='servicios.xlsx',
            as_attachment=True
        )

    except Exception as e:
        import traceback
        print("Error al generar Excel:", e)
        traceback.print_exc()
        return f"Error al generar el archivo Excel: {e}", 500

