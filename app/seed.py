import click

from app import db
from app.models import Role, Permission, Department, RequestType, User

PERMISSIONS = [
    ("manage_users", "Crear, editar y eliminar usuarios"),
    ("manage_roles", "Administrar roles, permisos y departamentos"),
    ("manage_documents", "Administrar todos los documentos (ver, eliminar)"),
    ("upload_documents", "Subir documentos a la intranet"),
    ("manage_requests", "Gestionar y dar seguimiento a solicitudes de otros"),
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


def _seed_data(log=print):
    """Crea las tablas e inserta datos base. Segura de llamar más de una vez."""
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

    if not User.query.filter_by(username="admin").first():
        admin_role = Role.query.filter_by(name="Administrador").first()
        admin = User(
            username="admin",
            full_name="Administrador del Sistema",
            email="admin@nexo-intranet.local",
            role_id=admin_role.id,
            department_id=deptos_obj["Sistemas"].id,
            is_active_user=True,
        )
        admin.set_password("Admin123!")
        db.session.add(admin)
        log("Usuario admin creado -> usuario: admin | contraseña: Admin123!")
    else:
        log("El usuario admin ya existía, no se modificó.")

    db.session.commit()
    log("Base de datos inicializada correctamente.")


def register_seed_command(app):
    @app.cli.command("seed-db")
    def seed_db():
        """Uso manual (si tienes Shell disponible): flask --app wsgi.py seed-db"""
        _seed_data(log=click.echo)