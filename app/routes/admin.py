from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import User, Role, Department, RequestType
from app.forms import UserForm, RoleForm, DepartmentForm
from app.decorators import permission_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/usuarios")
@login_required
@permission_required("manage_users")
def list_users():
    usuarios = User.query.order_by(User.full_name).all()
    return render_template("admin_users.html", usuarios=usuarios)


@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
@permission_required("manage_users")
def new_user():
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    form.department_id.choices = [(0, "-- Ninguno --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]

    if form.validate_on_submit():
        if not form.password.data:
            flash("La contraseña es obligatoria para un usuario nuevo.", "danger")
            return render_template("admin_user_form.html", form=form, modo="crear")

        if User.query.filter_by(username=form.username.data).first():
            flash("Ese nombre de usuario ya existe.", "danger")
            return render_template("admin_user_form.html", form=form, modo="crear")

        usuario = User(
            username=form.username.data.strip(),
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip(),
            role_id=form.role_id.data,
            department_id=form.department_id.data or None,
            is_active_user=form.is_active_user.data,
        )
        usuario.set_password(form.password.data)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("admin.list_users"))

    return render_template("admin_user_form.html", form=form, modo="crear")


@admin_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
@permission_required("manage_users")
def edit_user(user_id):
    usuario = User.query.get_or_404(user_id)
    form = UserForm(obj=usuario)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    form.department_id.choices = [(0, "-- Ninguno --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]

    if request.method == "GET":
        form.department_id.data = usuario.department_id or 0

    if form.validate_on_submit():
        usuario.username = form.username.data.strip()
        usuario.full_name = form.full_name.data.strip()
        usuario.email = form.email.data.strip()
        usuario.role_id = form.role_id.data
        usuario.department_id = form.department_id.data or None
        usuario.is_active_user = form.is_active_user.data
        if form.password.data:
            usuario.set_password(form.password.data)

        db.session.commit()
        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for("admin.list_users"))

    return render_template("admin_user_form.html", form=form, modo="editar", usuario=usuario)


@admin_bp.route("/usuarios/<int:user_id>/eliminar", methods=["POST"])
@login_required
@permission_required("manage_users")
def delete_user(user_id):
    if user_id == current_user.id:
        flash("No puedes eliminar tu propio usuario.", "danger")
        return redirect(url_for("admin.list_users"))

    usuario = User.query.get_or_404(user_id)
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado.", "info")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/roles")
@login_required
@permission_required("manage_roles")
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return render_template("admin_roles.html", roles=roles)


@admin_bp.route("/departamentos", methods=["GET", "POST"])
@login_required
@permission_required("manage_roles")
def list_departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        depto = Department(name=form.name.data.strip(), description=form.description.data)
        db.session.add(depto)
        db.session.commit()
        flash("Departamento creado.", "success")
        return redirect(url_for("admin.list_departments"))

    departamentos = Department.query.order_by(Department.name).all()
    return render_template("admin_departments.html", departamentos=departamentos, form=form)
