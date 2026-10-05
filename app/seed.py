import os
import uuid
import click
from sqlalchemy import inspect, text

from app import db
from app.models import Role, Permission, Department, RequestType, User, Document, ServiceRequest

PERMISSIONS = [
    ("manage_users", "Crear, editar y eliminar usuarios"),
    ("manage_roles", "Administrar roles, permisos y departamentos"),
    ("manage_documents", "Administrar todos los documentos (ver, eliminar)"),
    ("upload_documents", "Subir documentos a la intranet"),
    ("manage_requests", "Gestionar y dar seguimiento a solicitudes de otros"),
    ("delete_requests", "Eliminar solicitudes de forma permanente"),
]

ROLES = {
    "Administrador": [p[0] for p in PERMISSIONS],
    "Supervisor": ["upload_documents", "manage_requests"],
    "Empleado": ["upload_documents"],
}

DEPARTMENTS = [
    ("Sistemas", "Área de tecnología e infraestructura"),
    ("Recursos Humanos", "Gestión de personal y nómina"),
    ("Administración", "Administración general y finanzas"),
]

REQUEST_TYPES = [
    ("Solicitud de vacaciones", "Recursos Humanos"),
    ("Soporte técnico / TI", "Sistemas"),
    ("Compra de material", "Administración"),
    ("Constancia laboral", "Recursos Humanos"),
]

_TABLAS_CON_PUBLIC_ID = ["departments", "users", "documents", "service_requests"]
_MODELOS_CON_PUBLIC_ID = [Department, User, Document, ServiceRequest]


def _ensure_public_id_columns():
    """Agrega la columna public_id a tablas creadas antes de este cambio.
    Usa el inspector de SQLAlchemy en vez de 'IF NOT EXISTS' para que funcione
    igual en SQLite (desarrollo) y PostgreSQL (producción)."""
    inspector = inspect(db.engine)
    for tabla in _TABLAS_CON_PUBLIC_ID:
        if not inspector.has_table(tabla):
            continue  # la tabla se creará desde cero más abajo, ya con la columna
        columnas = [c["name"] for c in inspector.get_columns(tabla)]
        if "public_id" not in columnas:
            try:
                db.session.execute(text(f"ALTER TABLE {tabla} ADD COLUMN public_id VARCHAR(36)"))
                db.session.commit()
            except Exception:
                db.session.rollback()


def _backfill_public_ids():
    """Rellena public_id en filas que existían antes de este cambio."""
    for modelo in _MODELOS_CON_PUBLIC_ID:
        pendientes = modelo.query.filter(modelo.public_id.is_(None)).all()
        for fila in pendientes:
            fila.public_id = uuid.uuid4().hex
        if pendientes:
            db.session.commit()


def _crear_admin_inicial(deptos_obj, log):
    """Crea el administrador inicial SOLO si no existe ningún usuario con rol
    Administrador. Así, si el administrador definitivo tiene otro nombre
    (por ejemplo 'superadmin'), este usuario no reaparece en cada despliegue."""
    admin_role = Role.query.filter_by(name="Administrador").first()

    if User.query.filter_by(role_id=admin_role.id).first():
        log("Ya existe al menos un administrador; no se crea el usuario inicial.")
        return

    es_produccion = os.environ.get("FLASK_ENV", "development").lower() == "production"
    password = os.environ.get("ADMIN_INITIAL_PASSWORD") or (None if es_produccion else "Admin123!")

    if password is None:
        log("No hay administradores y ADMIN_INITIAL_PASSWORD no está definida: no se crea ninguno.")
        return

    admin = User(
        username="admin",
        full_name="Administrador del Sistema",
        email="admin@nexo-intranet.local",
        role_id=admin_role.id,
        department_id=deptos_obj["Sistemas"].id,
        is_active_user=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    log("Usuario administrador inicial creado: admin")


def _seed_data(log=print):
    """Crea las tablas e inserta datos base. Segura de llamar más de una vez."""
    _ensure_public_id_columns()
    db.create_all()
    _backfill_public_ids()

    permisos_obj = {}
    for code, desc in PERMISSIONS:
        perm = Permission.query.filter_by(code=code).first()
        if not perm:
            perm = Permission(code=code, description=desc)
            db.session.add(perm)
        permisos_obj[code] = perm
    db.session.flush()

    for role_name, perm_codes in ROLES.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"Rol {role_name}")
            db.session.add(role)
        role.permissions = [permisos_obj[c] for c in perm_codes]
    db.session.flush()

    deptos_obj = {}
    for name, desc in DEPARTMENTS:
        depto = Department.query.filter_by(name=name).first()
        if not depto:
            depto = Department(name=name, description=desc)
            db.session.add(depto)
        deptos_obj[name] = depto
    db.session.flush()

    for name, depto_name in REQUEST_TYPES:
        if not RequestType.query.filter_by(name=name).first():
            db.session.add(RequestType(name=name, department_id=deptos_obj[depto_name].id))

    _crear_admin_inicial(deptos_obj, log)

    db.session.commit()
    log("Base de datos inicializada correctamente.")


def register_seed_command(app):
    @app.cli.command("seed-db")
    def seed_db():
        _seed_data(log=click.echo)