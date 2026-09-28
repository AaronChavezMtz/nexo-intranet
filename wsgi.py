"""Punto de entrada usado por servidores WSGI de producción (gunicorn, uWSGI, etc.).

Ejemplo de arranque en producción:
    gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 3
"""
from app import create_app

app = create_app()
