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
    total_publishers = (
        models.Publisher
        .select(fn.COUNT(models.Publisher.id)
                .alias('total'))
    ).first().total
    total_datasets = (
        models.Publisher
        .select(fn.SUM(models.Publisher.total_datasets)
                .alias('total'))
    ).first().total
    total_pub_errors = (
        models.DatasetError
        .select(
            fn.COUNT(fn.DISTINCT(models.DatasetError.publisher_id))
            .alias('total'))
        .where(models.DatasetError.error_type != 'schema',
               models.DatasetError.last_status == 'fail')
    ).first().total
    total_dataset_errors = (
        models.DatasetError
        .select(
            fn.COUNT(models.DatasetError.id)
            .alias('total'))
        .where(models.DatasetError.error_type != 'schema',
               models.DatasetError.last_status == 'fail')
    ).first().total
    total_dataset_schema_errors = (
        models.DatasetError
        .select(
            fn.COUNT(models.DatasetError.id)
            .alias('total'))
        .where(models.DatasetError.error_type == 'schema',
               models.DatasetError.last_status == 'fail')
    ).first().total
    return render_template(
        'home.html',
        total_publishers=total_publishers,
        total_pub_errors=total_pub_errors,
        total_datasets=total_datasets,
        total_dataset_errors=total_dataset_errors,
        total_dataset_schema_errors=total_dataset_schema_errors)


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
    show_errors = request.args.get('errors', False) == 'true'

    if show_errors:
        publishers = (models.Publisher
                      .select(models.Publisher,
                              fn.COUNT(models.DatasetError.id)
                              .filter(models.DatasetError.error_type !=
                                      'schema')
                              .alias('error_count'))
                      .join(models.DatasetError, JOIN.LEFT_OUTER)
                      .where(models.Publisher.name.contains(search) |
                             models.Publisher.id.contains(search))
                      .group_by(models.Publisher.id)
                      .order_by(SQL('error_count').desc(),
                                models.Publisher.name)
                      .paginate(page, page_size))
        results = [{
            'id': p.id,
            'text': p.name,
            'error_count': p.error_count,
        } for p in publishers]
    else:
        publishers = (models.Publisher
                      .select()
                      .where(models.Publisher.name.contains(search) |
                             models.Publisher.id.contains(search))
                      .order_by(models.Publisher.name)
                      .paginate(page, page_size))
        results = [{
            'id': p.id,
            'text': p.name,
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
    errors = publisher.errors.where(models.DatasetError.error_type != 'schema')
    return render_template('publisher.html',
                           publisher=publisher,
                           errors=errors)
