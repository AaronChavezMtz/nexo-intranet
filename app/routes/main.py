from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models import Department, Document, RequestType, ServiceRequest

main_bp = Blueprint("main", __name__)

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]
SEMANAS_GRAFICA = 12


def _fecha_larga(d):
    # Sin depender del locale del servidor (Render no trae es_MX).
    return f"{_DIAS[d.weekday()]} {d.day} de {_MESES[d.month - 1]} de {d.year}"


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
    hoy = datetime.utcnow()
    contexto = {"mis_solicitudes": mis_solicitudes, "fecha_hoy": _fecha_larga(hoy),
                "tipos": RequestType.query.order_by(RequestType.name).all()}

    if not current_user.has_permission("manage_requests"):
        propias = ServiceRequest.query.filter_by(requester_id=current_user.id)
        contexto["conteos"] = {e: propias.filter_by(status=e).count() for e in ("Pendiente", "En proceso", "Aprobada")}
        # Misma regla de visibilidad que la lista de documentos.
        contexto["documentos"] = (
            Document.query.filter((Document.is_public == True) | (Document.department_id == current_user.department_id))  # noqa: E712
            .order_by(Document.uploaded_at.desc()).limit(5).all()
        )
        return render_template("dashboard.html", gestor=False, **contexto)

    abiertas = ServiceRequest.query.filter(ServiceRequest.status.in_(ServiceRequest.ABIERTAS))
    resueltas = db.session.query(ServiceRequest.created_at, ServiceRequest.updated_at).filter(
        ServiceRequest.status.in_(ServiceRequest.RESUELTAS)).all()
    dias_resolucion = [(fin - inicio).total_seconds() / 86400 for inicio, fin in resueltas if fin and inicio]

    # Volumen semanal: semanas completas de lunes a domingo, la última es la actual.
    lunes_actual = (hoy - timedelta(days=hoy.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    inicio = lunes_actual - timedelta(weeks=SEMANAS_GRAFICA - 1)
    semanas = [{"inicio": inicio + timedelta(weeks=i), "total": 0} for i in range(SEMANAS_GRAFICA)]
    for (creada,) in db.session.query(ServiceRequest.created_at).filter(ServiceRequest.created_at >= inicio):
        semanas[min((creada - inicio).days // 7, SEMANAS_GRAFICA - 1)]["total"] += 1

    por_estado = dict(db.session.query(ServiceRequest.status, db.func.count(ServiceRequest.id))
                      .group_by(ServiceRequest.status).all())
    por_area = (
        db.session.query(Department.name, db.func.count(ServiceRequest.id))
        .join(RequestType, RequestType.department_id == Department.id)
        .join(ServiceRequest, ServiceRequest.request_type_id == RequestType.id)
        .filter(ServiceRequest.status.in_(ServiceRequest.ABIERTAS))
        .group_by(Department.name)
        .order_by(db.func.count(ServiceRequest.id).desc())
        .all()
    )

    contexto.update(
        kpis={
            "abiertas": abiertas.count(),
            "sin_asignar": abiertas.filter(ServiceRequest.assigned_to_id.is_(None)).count(),
            "asignadas": abiertas.filter(ServiceRequest.assigned_to_id == current_user.id).count(),
            "resueltas_30": ServiceRequest.query.filter(
                ServiceRequest.status.in_(ServiceRequest.RESUELTAS),
                ServiceRequest.updated_at >= hoy - timedelta(days=30)).count(),
            "dias_promedio": sum(dias_resolucion) / len(dias_resolucion) if dias_resolucion else None,
        },
        semanas=semanas,
        por_estado=[(e, por_estado.get(e, 0)) for e in ServiceRequest.ESTADOS],
        por_area=por_area,
        atencion=(abiertas.filter(ServiceRequest.assigned_to_id.is_(None))
                  .order_by(ServiceRequest.created_at.asc()).limit(6).all()),
        hoy=hoy,
    )
    return render_template("dashboard.html", gestor=True, **contexto)
