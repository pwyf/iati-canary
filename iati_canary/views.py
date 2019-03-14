from flask import abort, Blueprint, render_template
from peewee import DoesNotExist, fn

from . import models


blueprint = Blueprint('iati_canary', __name__,
                      static_folder='../static')


@blueprint.route('/')
def home():
    publishers = models.Publisher.select().order_by(
        models.Publisher.last_checked.desc(nulls='LAST'))
    return render_template('home.html', publishers=publishers)


@blueprint.route('/publisher/<publisher_id>')
def publisher(publisher_id):
    try:
        publisher = models.Publisher.get_by_id(publisher_id)
    except DoesNotExist:
        return abort(404)
    return render_template('publisher.html', publisher=publisher)


@blueprint.route('/errors')
def errors():
    publishers = (models.Publisher
                  .select(models.Publisher,
                          fn.Count(models.DatasetError.id).alias('count'))
                  .join(models.DatasetError)
                  .where(models.DatasetError.error_type != 'schema error')
                  .group_by(models.Publisher)
                  .order_by(fn.Count(models.DatasetError.id).desc()))
    return render_template('errors.html', publishers=publishers)
