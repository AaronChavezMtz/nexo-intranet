web: gunicorn wsgi:app --workers 1 --bind 0.0.0.0:$PORT
release: flask --app wsgi.py seed-db
