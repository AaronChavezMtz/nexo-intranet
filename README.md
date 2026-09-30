# Nexo — Intranet Corporativa

Plataforma web para digitalizar procesos internos de una empresa: gestión documental,
solicitudes con flujo de aprobación y seguimiento, y administración de usuarios con
perfiles y permisos. Desarrollada con Python y Flask, con especial atención al control
de acceso, la seguridad de la aplicación y el diseño responsivo.

> Proyecto personal construido para practicar arquitectura de aplicaciones web,
> autenticación y autorización basada en roles, modelado de bases de datos
> relacionales y despliegue en producción.

---

## Tabla de contenido

- [Funcionalidades](#funcionalidades)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Modelo de datos](#modelo-de-datos)
- [Roles y permisos](#roles-y-permisos)
- [Instalación local](#instalación-local)
- [Variables de entorno](#variables-de-entorno)
- [Datos de ejemplo](#datos-de-ejemplo)
- [Despliegue en producción](#despliegue-en-producción)
- [Seguridad](#seguridad)
- [Roadmap](#roadmap)

---

## Funcionalidades

- **Autenticación y perfiles**: acceso por usuario/contraseña con contraseñas cifradas,
  roles (Administrador, Supervisor, Empleado) y permisos granulares por funcionalidad.
- **Gestión documental**: subir, categorizar, filtrar y descargar documentos, con
  visibilidad pública o restringida por departamento.
- **Solicitudes internas**: los colaboradores generan solicitudes con folio único;
  los responsables las asignan, actualizan su estado (Pendiente → En proceso →
  Aprobada/Rechazada/Cancelada) y dejan registro en una bitácora de seguimiento.
- **Panel de administración**: alta, edición y baja de usuarios (con eliminación en
  cascada de sus datos asociados), gestión de departamentos y consulta de roles/permisos.
- **Validación exhaustiva**: todos los formularios validan longitud, formato y campos
  obligatorios, mostrando errores específicos por campo.
- **Identificadores no secuenciales**: las URLs usan identificadores públicos (UUID)
  en lugar de IDs autoincrementales, evitando exponer el volumen de registros del sistema.
- **Interfaz responsiva** con una identidad visual corporativa propia (Bootstrap 5 + tipografía Inter).

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Servidor de producción | Gunicorn |
| Autenticación | Hash de contraseñas (Werkzeug `pbkdf2:sha256`), sesiones con Flask-Login |
| Control de versiones | Git / GitHub |
| Hosting | Render (Web Service + PostgreSQL administrado) |

## Arquitectura

El proyecto sigue el patrón **Application Factory** de Flask junto con **Blueprints**,
separando cada módulo funcional en su propio archivo:

```
nexo_intranet/
├── app/
│   ├── __init__.py          # Application factory, extensiones, manejo de errores
│   ├── models.py             # Modelos ORM (usuarios, roles, permisos, documentos, solicitudes)
│   ├── forms.py               # Formularios con validación (Flask-WTF)
│   ├── decorators.py          # Control de acceso por permisos
│   ├── seed.py                 # Datos base: roles, permisos, departamentos, usuario admin
│   ├── routes/
│   │   ├── auth.py             # Login, logout, cambio de contraseña
│   │   ├── main.py             # Dashboard
│   │   ├── documents.py        # Gestión documental
│   │   ├── requests.py         # Solicitudes: crear, listar, actualizar, eliminar
│   │   └── admin.py            # Usuarios, roles, departamentos
│   ├── templates/               # Vistas Jinja2 (HTML + Bootstrap 5)
│   └── static/                  # CSS, JS y documentos subidos
├── config.py                    # Configuración por entorno (desarrollo / producción)
├── run.py                       # Entrada para desarrollo local
├── wsgi.py                      # Entrada para servidores WSGI en producción
├── Procfile                     # Definición de proceso para plataformas cloud
└── requirements.txt
```

## Modelo de datos

| Entidad | Descripción |
|---|---|
| `User` | Colaborador: usuario, contraseña (hash), rol, departamento, estado activo/inactivo |
| `Role` / `Permission` | Perfiles y permisos del sistema (relación N:M) |
| `Department` | Áreas de la empresa |
| `Document` | Documentos con categoría, visibilidad y departamento asociado |
| `RequestType` | Catálogo de tipos de solicitud |
| `ServiceRequest` | Solicitud con folio, estado y responsable asignado |
| `RequestComment` | Bitácora de seguimiento de cada solicitud |

Todas las entidades principales (`User`, `Document`, `ServiceRequest`, `Department`)
usan un `public_id` (UUID) como identificador expuesto en la interfaz y en las URLs,
manteniendo el `id` autoincremental solo como clave interna de base de datos.

## Roles y permisos

| Rol | Permisos |
|---|---|
| **Administrador** | Gestión total: usuarios, roles, documentos, solicitudes (incluye eliminar) |
| **Supervisor** | Subir documentos, gestionar y actualizar solicitudes de su equipo |
| **Empleado** | Subir documentos propios, crear y dar seguimiento a sus propias solicitudes |

Los permisos se verifican mediante decoradores (`@permission_required`) en cada
ruta, no de forma implícita por el nombre del rol — esto permite agregar nuevos
roles o ajustar permisos sin tocar la lógica de las vistas.

## Instalación local

```bash
git clone https://github.com/AaronChavezMtz/nexo-intranet.git
cd nexo-intranet

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # define SECRET_KEY

flask --app run.py seed-db      # crea tablas, roles, permisos y usuario admin
python run.py
```

La aplicación queda disponible en `http://localhost:5000`.

**Usuario administrador inicial** (creado por `seed-db`):
- Usuario: `admin`
- Contraseña: `Admin123!`

> Cambia esta contraseña inmediatamente después del primer inicio de sesión,
> desde `Mi cuenta → Cambiar contraseña`.

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `FLASK_ENV` | Sí | `development` o `production` |
| `SECRET_KEY` | Sí en producción | Clave para firmar sesiones y formularios. Generar con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Sí en producción | Cadena de conexión a PostgreSQL |


## Despliegue en producción

El proyecto está preparado para desplegarse en **Render** (o cualquier plataforma
compatible con Gunicorn + PostgreSQL):

- `wsgi.py` expone la aplicación para el servidor WSGI y ejecuta automáticamente
  la inicialización de la base de datos al arrancar (sin necesidad de acceso a
  Shell, compatible con planes gratuitos).
- `Procfile` define el comando de arranque con Gunicorn.
- `config.py` separa la configuración de desarrollo y producción, exigiendo
  variables de entorno explícitas en producción en lugar de valores por defecto.

## Seguridad

- Contraseñas con hash `pbkdf2:sha256` (nunca en texto plano).
- Protección CSRF en todos los formularios (Flask-WTF).
- Control de acceso por permisos mediante decoradores, verificado en cada ruta.
- Cookies de sesión `HttpOnly`, `SameSite=Lax`, y `Secure` en producción.
- Identificadores públicos (UUID) en URLs en lugar de IDs autoincrementales.
- Validación de extensión y tamaño máximo de archivo al subir documentos.
- Eliminación en cascada controlada: borrar un usuario elimina de forma explícita
  sus documentos y solicitudes asociadas, evitando registros huérfanos.
- Confirmación explícita (modal) antes de cualquier acción destructiva.

## Roadmap

- Notificaciones por correo al cambiar el estado de una solicitud.
- Exportación de reportes (PDF/Excel) de solicitudes por periodo.
- Migraciones de esquema con Flask-Migrate/Alembic.
- API REST para integración con otras herramientas internas.
- Pruebas automatizadas con pytest.
- Panel de administración de roles y permisos vía interfaz (actualmente en `seed.py`).

---
