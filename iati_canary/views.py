from os.path import join

from flask import abort, Blueprint, render_template, send_from_directory, \
                  jsonify, request
from peewee import DoesNotExist, fn, JOIN

from . import models


blueprint = Blueprint('iati_canary', __name__,
                      static_folder='../static')


@blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(join('static', 'img'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@blueprint.route('/')
def home():
    return render_template('home.html')


@blueprint.route('/publishers')
def publishers():
    publishers = models.Publisher.select().order_by(
        models.Publisher.last_checked_at.desc(nulls='LAST'))
    return render_template('publishers.html', publishers=publishers)


@blueprint.route('/publishers.json')
def publishers_json():
    search = request.args.get('q', '')
    publishers = (models.Publisher
                  .select(models.Publisher,
                          fn.Count(models.DatasetError.id)
                          .alias('error_count'))
                  .join(models.DatasetError, JOIN.LEFT_OUTER)
                  .where((models.DatasetError.error_type.is_null()) |
                         (models.DatasetError.error_type != 'schema'),
                         models.Publisher.name.contains(search) |
                         models.Publisher.id.contains(search))
                  .group_by(models.Publisher)
                  .order_by(fn.Count(models.DatasetError.id).desc()))
    results = [{
        'id': p.id,
        'text': '{name} ({count} broken dataset{plural})'.format(
            name=p.name,
            count=p.error_count,
            plural='s' if p.error_count != 1 else '',
        ),
        'error_count': p.error_count,
    } for p in publishers]
    return jsonify({'results': results})


@blueprint.route('/publisher/<publisher_id>')
def publisher(publisher_id):
    try:
        publisher = models.Publisher.get_by_id(publisher_id)
    except DoesNotExist:
        return abort(404)
    return render_template('publisher.html', publisher=publisher)
