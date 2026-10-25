import os
import click

from flask import current_app

from app import db
from app.demo import seed_demo, restaurar_archivos_demo
from app.models import Role, Permission, Department, RequestType, User, Document

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

SUPERADMIN = "superadmin"


def _crear_admin_inicial(deptos_obj, log):
    """Crea la cuenta 'superadmin' SOLO si todavía no existe. Las cuentas demo
    también son administradoras, por eso se busca por nombre y no por rol."""
    admin_role = Role.query.filter_by(name="Administrador").first()

    if User.query.filter_by(username=SUPERADMIN).first():
        log("La cuenta superadmin ya existe; no se crea de nuevo.")
        return

    es_produccion = os.environ.get("FLASK_ENV", "development").lower() == "production"
    password = os.environ.get("ADMIN_INITIAL_PASSWORD") or (None if es_produccion else "Admin123!")

    if password is None:
        log("No hay administradores y ADMIN_INITIAL_PASSWORD no está definida: no se crea ninguno.")
        return

    admin = User(
        username=SUPERADMIN,
        full_name="Administrador del Sistema",
        email="superadmin@nexo-intranet.local",
        role_id=admin_role.id,
        department_id=deptos_obj["Sistemas"].id,
        is_active_user=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    log("Usuario administrador inicial creado: superadmin")


def _seed_data(log=print, conservados=()):
    """Crea las tablas e inserta datos base y demo. Segura de llamar más de una vez.
    'conservados' son cuentas que reset_demo vuelve a insertar tal como estaban."""
    db.create_all()

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

    roles_obj = {r.name: r for r in Role.query.all()}
    for c in conservados:
        db.session.add(User(
            public_id=c["public_id"], username=c["username"], email=c["email"],
            full_name=c["full_name"], password_hash=c["password_hash"], is_active_user=True,
            role_id=roles_obj[c["rol"]].id,
            department_id=deptos_obj[c["depto"]].id if c["depto"] in deptos_obj else None,
        ))

    _crear_admin_inicial(deptos_obj, log)

    db.session.commit()
    seed_demo(log)
    restaurar_archivos_demo()
    log("Base de datos inicializada correctamente.")


def reset_demo(log=print):
    """Borra TODAS las tablas y vuelve a crear la demo desde cero. Las cuentas
    protegidas (superadmin) se conservan con su contraseña y su sesión actual."""
    protegidos = current_app.config["PROTECTED_USERNAMES"]
    conservados = [
        {"public_id": u.public_id, "username": u.username, "email": u.email,
         "full_name": u.full_name, "password_hash": u.password_hash,
         "rol": u.role.name, "depto": u.department.name if u.department else None}
        for u in User.query.filter(User.username.in_(protegidos))
    ]

    carpeta = current_app.config["UPLOAD_FOLDER"]
    for (nombre,) in db.session.query(Document.stored_filename):
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            os.remove(ruta)

    db.session.remove()
    db.drop_all()
    _seed_data(log=log, conservados=conservados)


def register_seed_command(app):
    @app.cli.command("seed-db")
    def seed_db():
        _seed_data(log=click.echo)

    @app.cli.command("reset-demo")
    @click.confirmation_option(prompt="Esto BORRA todos los datos y recrea la demo. ¿Continuar?")
    def reset_demo_cmd():
        reset_demo(log=click.echo)