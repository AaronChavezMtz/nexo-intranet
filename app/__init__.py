import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = None
login_manager.login_message_category = "warning"


def create_app(config_class=None):
    """Crea y configura la instancia de la aplicación Flask (patrón factory)."""
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())

    # Necesario cuando la app corre detrás de un proxy inverso (Render, Railway,
    # Nginx, etc.) para que Flask reconozca correctamente el esquema (https) y la IP real.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.documents import documents_bp
    from app.routes.requests import requests_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(admin_bp)

    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from app.seed import register_seed_command
    register_seed_command(app)

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        app.logger.exception("Error interno del servidor")
        return render_template("errors/500.html"), 500

    return app
