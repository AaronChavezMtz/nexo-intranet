import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url):
    """Algunos proveedores (Render, Heroku, Railway) entregan 'postgres://',
    pero SQLAlchemy 2.x requiere el esquema 'postgresql://'."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Configuración base, común a todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'intranet.db')}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Fuera de 'static' para que los archivos solo se sirvan a través de la
    # vista de descarga, que verifica permisos y departamento.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB máximo por archivo
    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "png", "jpg", "jpeg", "txt", "csv",
    }

    # Cookies de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False   # se sobreescribe a True en producción (requiere HTTPS)
    REMEMBER_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo-local")


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Sin valor por defecto: en producción la base debe ser explícita.
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL"))

    @staticmethod
    def validate():
        faltantes = [v for v in ("SECRET_KEY", "DATABASE_URL") if not os.environ.get(v)]
        if faltantes:
            raise RuntimeError(
                f"Faltan variables de entorno obligatorias en producción: {', '.join(faltantes)}. "
                "No se usan valores por defecto en este entorno."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    cfg = config_by_name.get(env, DevelopmentConfig)
    validar = getattr(cfg, "validate", None)
    if validar:
        validar()
    return cfg