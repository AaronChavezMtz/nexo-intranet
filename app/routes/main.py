from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import RequestType, ServiceRequest

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

    # Quien gestiona solicitudes ve las cifras de la empresa; el resto, solo las suyas.
    gestor = current_user.has_permission("manage_requests")
    base = ServiceRequest.query if gestor else ServiceRequest.query.filter_by(requester_id=current_user.id)
    conteos = {e: base.filter_by(status=e).count() for e in ("Pendiente", "En proceso", "Aprobada")}

    asignadas_a_mi = []
    if gestor:
        asignadas_a_mi = (
            ServiceRequest.query.filter_by(assigned_to_id=current_user.id)
            .filter(ServiceRequest.status.in_(["Pendiente", "En proceso"]))
            .order_by(ServiceRequest.created_at.desc())
            .all()
        )

    return render_template(
        "dashboard.html",
        mis_solicitudes=mis_solicitudes,
        gestor=gestor,
        conteos=conteos,
        tipos=RequestType.query.order_by(RequestType.name).all(),
        asignadas_a_mi=asignadas_a_mi,
    )
