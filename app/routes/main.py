from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import Document, ServiceRequest, User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    mis_solicitudes = (
        ServiceRequest.query.filter_by(requester_id=current_user.id)
        .order_by(ServiceRequest.created_at.desc())
        .limit(5)
        .all()
    )

    total_documentos = Document.query.count()
    total_usuarios = User.query.count()

    pendientes = ServiceRequest.query.filter_by(status="Pendiente").count()
    en_proceso = ServiceRequest.query.filter_by(status="En proceso").count()

    asignadas_a_mi = []
    if current_user.has_permission("manage_requests"):
        asignadas_a_mi = (
            ServiceRequest.query.filter_by(assigned_to_id=current_user.id)
            .filter(ServiceRequest.status.in_(["Pendiente", "En proceso"]))
            .order_by(ServiceRequest.created_at.desc())
            .all()
        )

    return render_template(
        "dashboard.html",
        mis_solicitudes=mis_solicitudes,
        total_documentos=total_documentos,
        total_usuarios=total_usuarios,
        pendientes=pendientes,
        en_proceso=en_proceso,
        asignadas_a_mi=asignadas_a_mi,
    )
