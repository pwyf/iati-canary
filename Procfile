release: flask db upgrade
web: gunicorn canary.app:create_app\(\) -b 0.0.0.0:$PORT
