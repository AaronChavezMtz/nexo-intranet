import os
import uuid

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, send_from_directory, current_app, abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import Document, Department
from app.forms import DocumentForm
from app.decorators import permission_required

documents_bp = Blueprint("documents", __name__, url_prefix="/documentos")


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@documents_bp.route("/")
@login_required
def list_documents():
    query = Document.query
    categoria = request.args.get("categoria")
    if categoria:
        query = query.filter_by(category=categoria)

    if not current_user.has_permission("manage_documents"):
        query = query.filter(
            (Document.is_public == True) | (Document.department_id == current_user.department_id)  # noqa: E712
        )

    documentos = query.order_by(Document.uploaded_at.desc()).all()
    categorias = [c[0] for c in db.session.query(Document.category).distinct()]
    return render_template("documents.html", documentos=documentos, categorias=categorias)


@documents_bp.route("/subir", methods=["GET", "POST"])
@login_required
@permission_required("upload_documents")
def upload_document():
    form = DocumentForm()
    form.department_id.choices = [(0, "-- Ninguno / General --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]

    if form.validate_on_submit():
        file = form.file.data
        if not _allowed_file(file.filename):
            flash("Tipo de archivo no permitido.", "danger")
            return redirect(url_for("documents.upload_document"))

        ext = file.filename.rsplit(".", 1)[-1].lower()
        stored_filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename))

        doc = Document(
            title=form.title.data,
            description=form.description.data,
            original_filename=file.filename,
            stored_filename=stored_filename,
            category=form.category.data or "General",
            department_id=form.department_id.data or None,
            is_public=form.is_public.data,
            uploaded_by_id=current_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        flash("Documento subido correctamente.", "success")
        return redirect(url_for("documents.list_documents"))

    return render_template("upload_document.html", form=form)


@documents_bp.route("/<int:doc_id>/descargar")
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)

    puede_ver = (
        doc.is_public
        or current_user.has_permission("manage_documents")
        or doc.department_id == current_user.department_id
    )
    if not puede_ver:
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        doc.stored_filename,
        as_attachment=True,
        download_name=doc.original_filename,
    )


@documents_bp.route("/<int:doc_id>/eliminar", methods=["POST"])
@login_required
@permission_required("manage_documents")
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_filename)
    if os.path.exists(ruta):
        os.remove(ruta)
    db.session.delete(doc)
    db.session.commit()
    flash("Documento eliminado.", "info")
    return redirect(url_for("documents.list_documents"))
