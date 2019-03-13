from flask import abort, Blueprint, render_template
from peewee import DoesNotExist

from . import models


blueprint = Blueprint('iati_canary', __name__,
                      static_folder='../static')


@blueprint.route('/')
def home():
    return render_template('home.html', publishers=models.Publisher)


@blueprint.route('/publisher/<publisher_id>')
def publisher(publisher_id):
    try:
        publisher = models.Publisher.get_by_id(publisher_id)
    except DoesNotExist:
        return abort(404)
    return render_template('publisher.html', publisher=publisher)
