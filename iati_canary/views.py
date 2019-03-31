from os.path import join

from flask import abort, Blueprint, render_template, send_from_directory, \
                  jsonify, request
from peewee import DoesNotExist, fn, JOIN, SQL

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
    page_size = 20

    search = request.args.get('q', '')
    page = int(request.args.get('page', 1))

    publishers = (models.Publisher
                  .select(models.Publisher,
                          fn.COUNT(models.DatasetError.id)
                          .filter(models.DatasetError.error_type != 'schema')
                          .alias('error_count'))
                  .join(models.DatasetError, JOIN.LEFT_OUTER)
                  .where(models.Publisher.name.contains(search) |
                         models.Publisher.id.contains(search))
                  .group_by(models.Publisher.id)
                  .order_by(SQL('error_count').desc())
                  .paginate(page, page_size))

    results = [{
        'id': p.id,
        'text': '{name} ({count} broken dataset{plural})'.format(
            name=p.name,
            count=p.error_count,
            plural='s' if p.error_count != 1 else '',
        ) if p.error_count > 0 else p.name,
        'error_count': p.error_count,
    } for p in publishers]

    return jsonify({
        'results': results,
        'pagination': {
            'more': len(results) == page_size
        }
    })


@blueprint.route('/publisher/<publisher_id>')
def publisher(publisher_id):
    try:
        publisher = models.Publisher.get_by_id(publisher_id)
    except DoesNotExist:
        return abort(404)
    return render_template('publisher.html', publisher=publisher)
