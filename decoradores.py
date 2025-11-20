from functools import wraps
from flask import session, redirect, url_for, flash


def permiso_requerido(modulo, accion):
    """
    Ejemplo: @permiso_requerido("familiares", "editar")
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            if "id_usuario" not in session:
                flash("Debes iniciar sesión primero.", "warning")
                return redirect(url_for("login"))

            permisos = session.get("permisos", {})

            # Si es super admin, permitir todo
            if permisos.get("administrar_sistema"):
                return f(*args, **kwargs)

            # Verificar módulo
            if modulo not in permisos:
                flash("No tienes permiso para acceder a este módulo.", "danger")
                return redirect(url_for("dashboar"))

            # Verificar acción
            if not permisos[modulo].get(accion, False):
                flash("No tienes permiso para realizar esta acción.", "danger")
                return redirect(url_for("dashboar"))

            return f(*args, **kwargs)

        return wrapper

    return decorator
