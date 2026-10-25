import time

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User
from app.forms import LoginForm, ChangePasswordForm

auth_bp = Blueprint("auth", __name__)

# shortcut: contador en memoria del proceso, válido con un solo worker (Procfile/Render);
# con varios workers o instancias, pasar a un almacén compartido (p. ej. Flask-Limiter + Redis).
# Se cuenta por IP y no por usuario para que nadie pueda bloquear la cuenta de otro.
MAX_INTENTOS = 10
VENTANA_SEG = 15 * 60
_intentos_fallidos = {}  # ip -> marcas de tiempo de los fallos recientes


def _bloqueado(ip) -> bool:
    ahora = time.monotonic()
    recientes = [t for t in _intentos_fallidos.get(ip, []) if ahora - t < VENTANA_SEG]
    if recientes:
        _intentos_fallidos[ip] = recientes
    else:
        _intentos_fallidos.pop(ip, None)
    return len(recientes) >= MAX_INTENTOS


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        ip = request.remote_addr  # IP real del cliente gracias a ProxyFix
        if _bloqueado(ip):
            flash("Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=form.username.data.strip()).first()

        if user is None or not user.check_password(form.password.data):
            _intentos_fallidos.setdefault(ip, []).append(time.monotonic())
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active_user:
            flash("Tu cuenta se encuentra desactivada. Contacta al administrador.", "danger")
            return redirect(url_for("auth.login"))

        _intentos_fallidos.pop(ip, None)
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        # Solo rutas internas: evita que un enlace manipulado lleve a otro sitio tras el login.
        if not next_page or not next_page.startswith("/") or next_page.startswith("//") or "\\" in next_page:
            next_page = url_for("main.dashboard")
        return redirect(next_page)
    elif request.method == "POST":
        flash("Escribe tu usuario y contraseña.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/mi-cuenta/cambiar-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("La contraseña actual no es correcta.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("main.dashboard"))
    elif request.method == "POST":
        flash("No se pudo cambiar la contraseña: revisa los campos marcados en rojo.", "danger")
    return render_template("change_password.html", form=form)
