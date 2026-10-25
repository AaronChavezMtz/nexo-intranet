import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_DEFAULT_DB = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'intranet.db')}"


class Config:
    """Configuración base, común a todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _DEFAULT_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_recycle: Azure SQL cierra conexiones inactivas tras ~30 min.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}

    # Fuera de 'static' para que los archivos solo se sirvan a través de la
    # vista de descarga, que verifica permisos y departamento.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB máximo por archivo
    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "png", "jpg", "jpeg", "txt", "csv",
    }

    # Usuarios protegidos: solo ellos mismos pueden editarse; nadie puede eliminarlos,
    # renombrarlos, desactivarlos ni cambiarles el rol. Lista separada por comas.
    PROTECTED_USERNAMES = {"superadmin"} | {
        u.strip() for u in os.environ.get("PROTECTED_USERNAMES", "").split(",") if u.strip()
    }

    # Cookies de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False   # se sobreescribe a True en producción (requiere HTTPS)
    REMEMBER_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave-solo-para-desarrollo-local"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Sin valor por defecto: en producción la base debe ser explícita.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

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