from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models import ServiceRequest, RequestType, RequestComment, User
from app.forms import ServiceRequestForm, RequestUpdateForm
from app.decorators import permission_required

requests_bp = Blueprint("requests", __name__, url_prefix="/solicitudes")


def _generar_folio() -> str:
    total = ServiceRequest.query.count() + 1
    return f"SOL-{total:05d}"


@requests_bp.route("/")
@login_required
def list_requests():
    if current_user.has_permission("manage_requests"):
        estado = request.args.get("estado")
        query = ServiceRequest.query
        if estado:
            query = query.filter_by(status=estado)
        solicitudes = query.order_by(ServiceRequest.created_at.desc()).all()
    else:
        solicitudes = (
            ServiceRequest.query.filter_by(requester_id=current_user.id)
            .order_by(ServiceRequest.created_at.desc())
            .all()
        )

    return render_template("requests_list.html", solicitudes=solicitudes)


@requests_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def new_request():
    form = ServiceRequestForm()
    form.request_type_id.choices = [
        (t.id, t.name) for t in RequestType.query.order_by(RequestType.name).all()
    ]

    if form.validate_on_submit():
        solicitud = ServiceRequest(
            folio=_generar_folio(),
            request_type_id=form.request_type_id.data,
            requester_id=current_user.id,
            description=form.description.data,
            status="Pendiente",
        )
        db.session.add(solicitud)
        db.session.flush()

        primer_comentario = RequestComment(
            service_request_id=solicitud.id,
            user_id=current_user.id,
            comment="Solicitud creada.",
            new_status="Pendiente",
        )
        db.session.add(primer_comentario)
        db.session.commit()

        flash(f"Solicitud {solicitud.folio} creada correctamente.", "success")
        return redirect(url_for("requests.view_request", request_id=solicitud.public_id))

    return render_template("new_request.html", form=form)


@requests_bp.route("/<string:request_id>", methods=["GET", "POST"])
@login_required
def view_request(request_id):
    solicitud = ServiceRequest.query.filter_by(public_id=request_id).first_or_404()

    es_dueno = solicitud.requester_id == current_user.id
    puede_gestionar = current_user.has_permission("manage_requests")
    if not (es_dueno or puede_gestionar):
        abort(403)

    update_form = None
    if puede_gestionar:
        update_form = RequestUpdateForm()
        update_form.assigned_to_id.choices = [(0, "-- Sin asignar --")] + [
            (u.id, u.full_name) for u in User.query.order_by(User.full_name).all()
        ]
        update_form.status.data = solicitud.status
        update_form.assigned_to_id.data = solicitud.assigned_to_id or 0

        if update_form.validate_on_submit():
            estado_anterior = solicitud.status
            solicitud.status = update_form.status.data
            solicitud.assigned_to_id = update_form.assigned_to_id.data or None

            comentario = RequestComment(
                service_request_id=solicitud.id,
                user_id=current_user.id,
                comment=update_form.comment.data,
                new_status=update_form.status.data if update_form.status.data != estado_anterior else None,
            )
            db.session.add(comentario)
            db.session.commit()
            flash("Solicitud actualizada.", "success")
            return redirect(url_for("requests.view_request", request_id=solicitud.public_id))
        elif request.method == "POST":
            flash("No se pudo actualizar: revisa los campos marcados en rojo.", "danger")

    return render_template("request_detail.html", solicitud=solicitud, update_form=update_form)