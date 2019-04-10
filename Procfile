release: flask db upgrade
web: gunicorn iati_canary.app:create_app\(\) -b 0.0.0.0:$PORT
worker: flask refresh-schemas && flask validate
