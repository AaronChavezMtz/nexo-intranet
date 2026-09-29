from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.seed import _seed_data

app = create_app()

# En el plan gratuito de Render no hay acceso a Shell, así que la app
# inicializa sus propias tablas y datos base la primera vez que arranca.
with app.app_context():
    try:
        _seed_data(log=app.logger.info)
    except IntegrityError:
        db.session.rollback()
        app.logger.info("Datos base ya existían (creados por otro proceso).")
    except Exception:
        db.session.rollback()
        app.logger.exception("No se pudo inicializar la base de datos automáticamente.")