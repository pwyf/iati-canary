from flask import Flask

from . import views
from .extensions import db


def create_app(config_object='iati_canary.settings'):
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    app.register_blueprint(views.blueprint)
    db.init_app(app)
    return app
