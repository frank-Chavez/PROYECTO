from functools import wraps
from flask import session, redirect, url_for, flash


def permiso_requerido(nombre_permiso):
    """
    Decorador para verificar si el usuario tiene un permiso específico.
    Ejemplo: @permiso_requerido("editar_registros")
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Si no está logueado, lo mandamos al login
            if "id_usuario" not in session:
                flash("Debes iniciar sesión primero.", "warning")
                return redirect(url_for("login"))

            permisos = session.get("permisos", {})

            # Si el permiso no existe o es 0, lo redirigimos al dashboard
            if not permisos.get(nombre_permiso, 0):
                flash("No tienes permiso para acceder a esta sección.", "danger")
                return redirect(url_for("dashboar"))  # ajusta si tu dashboard tiene otro nombre

            # Si todo ok, continúa la ejecución normal
            return f(*args, **kwargs)

        return wrapper

    return decorator
