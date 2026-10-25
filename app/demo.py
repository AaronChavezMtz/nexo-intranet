"""Datos de ejemplo de la versión demo: cuentas de prueba, empleados,
solicitudes con comentarios y documentos."""
import os
import random
import secrets
import shutil
import unicodedata
import uuid
from datetime import datetime, timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from app import db
from app.models import Role, Department, RequestType, User, Document, ServiceRequest, RequestComment

ARCHIVO_EJEMPLO = os.path.join(os.path.dirname(__file__), "demo_data", "documento_ejemplo.txt")

# Cuentas publicadas en el README para que cualquiera pueda probar la demo.
CUENTAS_DEMO = [
    ("adminprueba", "123_Admin", "Administrador de Prueba", "Administrador", "Sistemas"),
    ("supervisorprueba", "Supervisor1234", "Supervisor de Prueba", "Supervisor", "Recursos Humanos"),
    ("ana.garcia", "Empleado1234", "Ana García", "Empleado", "Administración"),
]
# Son públicas: nadie puede cambiarles la contraseña o la demo quedaría bloqueada.
USUARIOS_DEMO = frozenset(c[0] for c in CUENTAS_DEMO)

TOTAL_EMPLEADOS = 30
TOTAL_SOLICITUDES = 80

NOMBRES = [
    "Luis", "María", "José", "Fernanda", "Carlos", "Sofía", "Miguel", "Valeria", "Jorge", "Daniela",
    "Ricardo", "Paola", "Andrés", "Gabriela", "Eduardo", "Mariana", "Héctor", "Lucía", "Raúl", "Camila",
    "Óscar", "Natalia", "Alejandro", "Ximena", "Fernando", "Regina", "Sergio", "Andrea", "Javier", "Diana",
]
APELLIDOS = [
    "Hernández", "López", "Martínez", "González", "Pérez", "Rodríguez", "Sánchez", "Ramírez", "Torres",
    "Flores", "Rivera", "Gómez", "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez", "Ortiz", "Mendoza",
    "Castillo", "Vargas", "Romero", "Jiménez", "Ruiz", "Aguilar", "Medina", "Chávez", "Ramos",
]

# (título, nombre de archivo, categoría, departamento, público)
DOCUMENTOS = [
    ("Política de vacaciones 2026", "politica_vacaciones_2026.txt", "Políticas", "Recursos Humanos", True),
    ("Reglamento interior de trabajo", "reglamento_interior.txt", "Políticas", "Recursos Humanos", True),
    ("Formato de solicitud de permiso", "formato_permiso.txt", "Formatos", "Recursos Humanos", True),
    ("Calendario de nómina", "calendario_nomina.txt", "General", "Recursos Humanos", True),
    ("Expedientes: lineamientos de resguardo", "lineamientos_expedientes.txt", "Políticas", "Recursos Humanos", False),
    ("Manual de uso del correo institucional", "manual_correo.txt", "Manuales", "Sistemas", True),
    ("Política de contraseñas y seguridad", "politica_seguridad.txt", "Políticas", "Sistemas", True),
    ("Guía de conexión a la VPN", "guia_vpn.txt", "Manuales", "Sistemas", True),
    ("Inventario de equipos de cómputo", "inventario_equipos.txt", "Reportes", "Sistemas", False),
    ("Plan de respaldos", "plan_respaldos.txt", "Manuales", "Sistemas", False),
    ("Procedimiento de compras", "procedimiento_compras.txt", "Políticas", "Administración", True),
    ("Formato de requisición de material", "formato_requisicion.txt", "Formatos", "Administración", True),
    ("Lineamientos de viáticos", "lineamientos_viaticos.txt", "Políticas", "Administración", True),
    ("Reporte de gastos trimestral", "reporte_gastos_t3.txt", "Reportes", "Administración", False),
    ("Directorio de proveedores", "directorio_proveedores.txt", "General", "Administración", False),
]

DESCRIPCIONES = {
    "Solicitud de vacaciones": [
        "Solicito {n} días de vacaciones a partir del próximo lunes.",
        "Requiero vacaciones del periodo pendiente, {n} días hábiles.",
        "Quisiera tomar {n} días de vacaciones por un viaje familiar.",
    ],
    "Soporte técnico / TI": [
        "Mi equipo no enciende desde esta mañana.",
        "No puedo acceder a la carpeta compartida del área.",
        "La impresora del piso marca error de papel atascado.",
        "Necesito instalar el software de hojas de cálculo en mi equipo.",
        "Olvidé mi contraseña del correo institucional.",
    ],
    "Compra de material": [
        "Se requieren {n} paquetes de hojas tamaño carta para el área.",
        "Solicito {n} tóners para la impresora del departamento.",
        "Necesitamos {n} sillas ergonómicas para los nuevos ingresos.",
    ],
    "Constancia laboral": [
        "Solicito constancia laboral para trámite de crédito.",
        "Requiero constancia de antigüedad para trámite personal.",
        "Necesito constancia laboral con sueldo para renta de vivienda.",
    ],
}

COMENTARIOS = {
    "En proceso": ["Recibido, ya lo estamos revisando.", "Se asignó al área correspondiente.",
                   "En revisión, te contactamos en breve."],
    "Aprobada": ["Aprobada. Queda registrada en el sistema.", "Listo, se autorizó la solicitud.",
                 "Atendida y cerrada. Gracias."],
    "Rechazada": ["No procede por falta de presupuesto este mes.", "Rechazada: faltan datos en la solicitud.",
                  "No es posible en las fechas solicitadas."],
    "Cancelada": ["Ya no es necesaria, la cancelo.", "Se resolvió por otro medio, gracias."],
}

# Estados intermedios por los que pasa una solicitud hasta su estado final.
PASOS = {
    "Pendiente": [],
    "En proceso": ["En proceso"],
    "Aprobada": ["En proceso", "Aprobada"],
    "Rechazada": ["En proceso", "Rechazada"],
    "Cancelada": ["Cancelada"],
}


def _sin_acentos(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def restaurar_archivos_demo():
    """Copia el archivo de ejemplo para cada documento demo que no tenga archivo.
    En Render el disco es efímero y los archivos se pierden en cada despliegue."""
    carpeta = current_app.config["UPLOAD_FOLDER"]
    for (nombre,) in db.session.query(Document.stored_filename).filter(Document.stored_filename.like("demo-%")):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            shutil.copyfile(ARCHIVO_EJEMPLO, ruta)


def seed_demo(log=print):
    """Inserta los datos demo solo en una base que aún no los tiene."""
    if User.query.filter_by(username=CUENTAS_DEMO[0][0]).first() or ServiceRequest.query.first():
        return

    rnd = random.Random(42)  # semilla fija: la demo queda igual en cada reinicio
    ahora = datetime.utcnow()
    roles = {r.name: r for r in Role.query.all()}
    deptos = {d.name: d for d in Department.query.all()}

    usuarios = []
    for username, password, nombre, rol, depto in CUENTAS_DEMO:
        u = User(username=username, email=f"{username}@nexo-intranet.mx", full_name=nombre,
                 role_id=roles[rol].id, department_id=deptos[depto].id, is_active_user=True,
                 created_at=ahora - timedelta(days=400))
        u.set_password(password)
        usuarios.append(u)

    # Los empleados generados no tienen una contraseña conocida: solo son datos de ejemplo.
    hash_sin_acceso = generate_password_hash(secrets.token_urlsafe(32))
    usados = {u.username for u in usuarios}
    generados = 0
    while generados < TOTAL_EMPLEADOS:
        nombre, apellido = rnd.choice(NOMBRES), rnd.choice(APELLIDOS)
        username = _sin_acentos(f"{nombre}.{apellido}").lower()
        if username in usados:
            continue
        usados.add(username)
        usuarios.append(User(
            username=username, email=f"{username}@nexo-intranet.mx", full_name=f"{nombre} {apellido}",
            password_hash=hash_sin_acceso,
            role_id=roles["Supervisor" if generados < 4 else "Empleado"].id,
            department_id=rnd.choice(list(deptos.values())).id,
            is_active_user=generados < TOTAL_EMPLEADOS - 2,
            created_at=ahora - timedelta(days=rnd.randint(30, 365)),
        ))
        generados += 1
    db.session.add_all(usuarios)
    db.session.flush()

    gestores = [u for u in usuarios if u.role_id in (roles["Supervisor"].id, roles["Administrador"].id)]
    solicitantes = [u for u in usuarios if u.is_active_user]
    tipos = RequestType.query.all()

    for i in range(1, TOTAL_SOLICITUDES + 1):
        tipo, solicitante = rnd.choice(tipos), rnd.choice(solicitantes)
        estado = rnd.choices(ServiceRequest.ESTADOS, weights=[3, 3, 4, 2, 1])[0]
        momento = creada = ahora - timedelta(days=rnd.randint(1, 120), hours=rnd.randint(0, 23))
        gestor = rnd.choice(gestores)

        comentarios = [RequestComment(user_id=solicitante.id, comment="Solicitud creada.",
                                      new_status="Pendiente", created_at=creada)]
        for paso in PASOS[estado]:
            momento = min(momento + timedelta(hours=rnd.randint(2, 72)), ahora)
            autor = solicitante if paso == "Cancelada" else gestor
            comentarios.append(RequestComment(user_id=autor.id, comment=rnd.choice(COMENTARIOS[paso]),
                                              new_status=paso, created_at=momento))

        db.session.add(ServiceRequest(
            folio=f"SOL-{i:05d}", request_type_id=tipo.id, requester_id=solicitante.id,
            assigned_to_id=gestor.id if estado not in ("Pendiente", "Cancelada") else None,
            description=rnd.choice(DESCRIPCIONES[tipo.name]).format(n=rnd.randint(2, 10)),
            status=estado, created_at=creada, updated_at=momento, comments=comentarios,
        ))

    for titulo, archivo, categoria, depto, publico in DOCUMENTOS:
        del_area = [u for u in usuarios if u.department_id == deptos[depto].id and u.is_active_user]
        db.session.add(Document(
            title=titulo, description=f"Documento de ejemplo del área de {depto}.",
            original_filename=archivo, stored_filename=f"demo-{uuid.uuid4().hex}.txt",
            category=categoria, department_id=deptos[depto].id, is_public=publico,
            uploaded_by_id=rnd.choice(del_area).id,
            uploaded_at=ahora - timedelta(days=rnd.randint(1, 200)),
        ))

    db.session.commit()
    log(f"Datos demo creados: {len(usuarios)} usuarios, {TOTAL_SOLICITUDES} solicitudes, {len(DOCUMENTOS)} documentos.")
