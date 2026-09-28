# Nexo — Intranet corporativa

Plataforma web para digitalizar procesos internos de una empresa: gestión documental,
solicitudes con flujo de aprobación y seguimiento, y administración de usuarios con
perfiles y permisos. Proyecto personal construido con Python (Flask) para practicar
arquitectura de aplicaciones web, control de acceso y diseño de bases de datos relacionales.

## Funcionalidades

- **Autenticación y perfiles**: acceso por usuario/contraseña con roles (Administrador,
  Supervisor, Empleado) y permisos granulares por funcionalidad.
- **Gestión documental**: subir, categorizar, filtrar y descargar documentos, con
  visibilidad pública o restringida por departamento.
- **Solicitudes internas**: los colaboradores generan solicitudes (folio único) que
  los responsables pueden asignar, aprobar/rechazar y dar seguimiento mediante una
  bitácora de cambios de estado.
- **Panel de administración**: alta y edición de usuarios, consulta de roles/permisos
  y gestión de departamentos.
- **Interfaz responsiva** con Bootstrap 5.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| Base de datos | SQLite en desarrollo / PostgreSQL en producción |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Servidor de producción | Gunicorn |
| Autenticación | Hash de contraseñas (Werkzeug), sesiones con Flask-Login |
| Control de versiones | Git |

## Arquitectura

Patrón **Application Factory** + **Blueprints**, separando el proyecto en módulos
independientes:

```
nexo_intranet/
├── app/
│   ├── __init__.py          # Application factory, extensiones, manejo de errores
│   ├── models.py             # Modelos ORM (usuarios, roles, permisos, documentos, solicitudes)
│   ├── forms.py               # Formularios con validación (Flask-WTF)
│   ├── decorators.py          # Control de acceso por permisos
│   ├── seed.py                 # Comando `flask seed-db`: datos iniciales
│   ├── routes/                 # Blueprints: auth, main, documents, requests, admin
│   ├── templates/               # Vistas Jinja2 (HTML + Bootstrap 5)
│   └── static/                  # CSS, JS y documentos subidos
├── config.py                    # Configuración por entorno (desarrollo / producción)
├── run.py                       # Entrada para desarrollo local
├── wsgi.py                      # Entrada para servidores WSGI en producción
├── Procfile                     # Definición de proceso para plataformas cloud
└── requirements.txt
```

### Modelo de datos (resumen)

- **User** — colaborador con rol, departamento y estado (activo/inactivo).
- **Role / Permission** — perfiles y permisos (relación N:M).
- **Department** — áreas de la empresa.
- **Document** — documentos con categoría, visibilidad y departamento asociado.
- **RequestType / ServiceRequest / RequestComment** — catálogo de solicitudes, folio,
  estado y bitácora de seguimiento.

## Ejecución en local

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # define SECRET_KEY
flask --app run.py seed-db      # crea tablas, roles, permisos y usuario admin
python run.py
```

Disponible en `http://localhost:5000`. El comando `seed-db` crea un usuario `admin`
con contraseña `Admin123!` (cámbiala inmediatamente tras el primer inicio de sesión).

## Seguridad implementada

- Contraseñas con hash `pbkdf2:sha256` (nunca en texto plano).
- Protección CSRF en todos los formularios.
- Control de acceso por permisos mediante decoradores, no por rutas sueltas.
- Cookies de sesión `HttpOnly`, `SameSite=Lax`, y `Secure` en producción.
- Validación de extensión y tamaño máximo de archivo al subir documentos.
- Configuración separada por entorno (`development` / `production`) para evitar
  usar valores de desarrollo (como `debug=True`) en un entorno público.

## Roadmap / mejoras futuras

- Notificaciones por correo al cambiar el estado de una solicitud.
- Exportación de reportes (PDF/Excel).
- Migraciones de esquema con Flask-Migrate/Alembic.
- API REST para integración con otras herramientas.
- Pruebas automatizadas con pytest.
