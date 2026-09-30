import os

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User, Role, Department, RequestType, Document, ServiceRequest, RequestComment
from app.forms import UserForm, RoleForm, DepartmentForm
from app.decorators import permission_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------ Usuarios ------------------------------
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

        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Ese nombre de usuario ya existe.", "danger")
            return render_template("admin_user_form.html", form=form, modo="crear")

        if User.query.filter_by(email=form.email.data.strip()).first():
            flash("Ese correo ya está registrado por otro usuario.", "danger")
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
    elif request.method == "POST":
        flash("No se pudo guardar: revisa los campos marcados en rojo.", "danger")

    return render_template("admin_user_form.html", form=form, modo="crear")


@admin_bp.route("/usuarios/<string:user_id>/editar", methods=["GET", "POST"])
@login_required
@permission_required("manage_users")
def edit_user(user_id):
    usuario = User.query.filter_by(public_id=user_id).first_or_404()
    form = UserForm(obj=usuario)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]
    form.department_id.choices = [(0, "-- Ninguno --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]

    if request.method == "GET":
        form.department_id.data = usuario.department_id or 0
        form.password.data = ""
        form.confirm_password.data = ""

    if form.validate_on_submit():
        username_dup = User.query.filter(
            User.username == form.username.data.strip(), User.id != usuario.id
        ).first()
        email_dup = User.query.filter(
            User.email == form.email.data.strip(), User.id != usuario.id
        ).first()

        if username_dup:
            flash("Ese nombre de usuario ya lo usa otra persona.", "danger")
        elif email_dup:
            flash("Ese correo ya lo usa otra persona.", "danger")
        else:
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
    elif request.method == "POST":
        flash("No se pudo guardar: revisa los campos marcados en rojo.", "danger")

    return render_template("admin_user_form.html", form=form, modo="editar", usuario=usuario)


@admin_bp.route("/usuarios/<string:user_id>/eliminar", methods=["POST"])
@login_required
@permission_required("manage_users")
def delete_user(user_id):
    usuario = User.query.filter_by(public_id=user_id).first_or_404()

    if usuario.id == current_user.id:
        flash("No puedes eliminar tu propio usuario.", "danger")
        return redirect(url_for("admin.list_users"))

    try:
        # 1. Elimina los documentos que subió (y su archivo físico en el servidor)
        for doc in Document.query.filter_by(uploaded_by_id=usuario.id).all():
            ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_filename)
            if os.path.exists(ruta):
                os.remove(ruta)
            db.session.delete(doc)

        # 2. Elimina comentarios que dejó en solicitudes de otras personas
        RequestComment.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)

        # 3. Si era supervisor de solicitudes ajenas, las deja sin asignar (no las borra)
        ServiceRequest.query.filter_by(assigned_to_id=usuario.id).update(
            {"assigned_to_id": None}, synchronize_session=False
        )

        # 4. Elimina las solicitudes que él mismo creó (arrastra su propia bitácora)
        for sol in ServiceRequest.query.filter_by(requester_id=usuario.id).all():
            db.session.delete(sol)

        db.session.delete(usuario)
        db.session.commit()
        flash(f"Usuario '{usuario.full_name}' y todos sus datos asociados fueron eliminados.", "info")
    except IntegrityError:
        db.session.rollback()
        flash("No se pudo eliminar el usuario: hay datos relacionados que lo impiden.", "danger")

    return redirect(url_for("admin.list_users"))


# ------------------------------ Roles ------------------------------
@admin_bp.route("/roles")
@login_required
@permission_required("manage_roles")
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return render_template("admin_roles.html", roles=roles)


# ------------------------------ Departamentos ------------------------------
@admin_bp.route("/departamentos", methods=["GET", "POST"])
@login_required
@permission_required("manage_roles")
def list_departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        nombre = form.name.data.strip()
        if Department.query.filter_by(name=nombre).first():
            flash("Ya existe un departamento con ese nombre.", "danger")
        else:
            depto = Department(name=nombre, description=(form.description.data or "").strip())
            db.session.add(depto)
            db.session.commit()
            flash("Departamento creado.", "success")
            return redirect(url_for("admin.list_departments"))
    elif request.method == "POST":
        flash("No se pudo guardar: revisa los campos marcados en rojo.", "danger")

    departamentos = Department.query.order_by(Department.name).all()
    return render_template("admin_departments.html", departamentos=departamentos, form=form)


@admin_bp.route("/departamentos/<string:dept_id>/editar", methods=["GET", "POST"])
@login_required
@permission_required("manage_roles")
def edit_department(dept_id):
    depto = Department.query.filter_by(public_id=dept_id).first_or_404()
    form = DepartmentForm(obj=depto)

    if form.validate_on_submit():
        nombre = form.name.data.strip()
        duplicado = Department.query.filter(
            Department.name == nombre, Department.id != depto.id
        ).first()
        if duplicado:
            flash("Ya existe otro departamento con ese nombre.", "danger")
        else:
            depto.name = nombre
            depto.description = (form.description.data or "").strip()
            db.session.commit()
            flash("Departamento actualizado.", "success")
            return redirect(url_for("admin.list_departments"))
    elif request.method == "POST":
        flash("No se pudo guardar: revisa los campos marcados en rojo.", "danger")

    return render_template("admin_department_form.html", form=form, depto=depto)


@admin_bp.route("/departamentos/<string:dept_id>/eliminar", methods=["POST"])
@login_required
@permission_required("manage_roles")
def delete_department(dept_id):
    depto = Department.query.filter_by(public_id=dept_id).first_or_404()
    try:
        db.session.delete(depto)
        db.session.commit()
        flash("Departamento eliminado.", "info")
    except IntegrityError:
        db.session.rollback()
        flash(
            "No se puede eliminar: hay usuarios, documentos o tipos de solicitud "
            "asignados a este departamento.",
            "danger",
        )
    return redirect(url_for("admin.list_departments"))