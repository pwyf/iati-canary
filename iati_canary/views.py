from os.path import join

from flask import abort, Blueprint, render_template, send_from_directory, \
                  jsonify, request, redirect, url_for, flash
from sqlalchemy_mixins import ModelNotFoundError

from . import models
from .extensions import db
from .forms import SignupForm


blueprint = Blueprint('iati_canary', __name__,
                      static_folder='../static')


@blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(join('static', 'img'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    form = SignupForm()
    if form.validate_on_submit():
        flash('Sign up isn’t possible yet. Sorry!', 'danger')
        return redirect(url_for('iati_canary.home') + '#sign-up')

    total_publishers = models.Publisher.query.count()
    total_datasets = db.session.query(
        db.func.SUM(models.Publisher.total_datasets)
    ).first()[0]
    total_datasets = total_datasets if total_datasets else 0
    pub_errors = (models.DownloadError
                  .where(currently_erroring=True)
                  .distinct(models.DownloadError.publisher_id)
                  .all()
                  ) + \
                 (models.XMLError
                  .where(currently_erroring=True)
                  .distinct(models.XMLError.publisher_id)
                  .all()
                  )
    total_pub_errors = len(set([err.publisher_id for err in pub_errors]))
    total_download_errors = (models.DownloadError
                             .where(currently_erroring=True)
                             .count()
                             )
    total_xml_errors = (models.XMLError
                        .where(currently_erroring=True)
                        .count()
                        )
    total_dataset_errors = total_download_errors + total_xml_errors
    total_dataset_schema_errors = (models.ValidationError
                                   .where(currently_erroring=True)
                                   .count()
                                   )
    numbers = {
        'total_publishers': total_publishers,
        'total_datasets': total_datasets,
        'total_pub_errors': total_pub_errors,
        'total_dataset_errors': total_dataset_errors,
        'total_dataset_schema_errors': total_dataset_schema_errors,
    }
    return render_template(
        'home.html',
        numbers=numbers,
        form=form,
    )


@blueprint.route('/publishers')
def publishers():
    publishers = models.Publisher.all()
    return render_template('publishers.html', publishers=publishers)


@blueprint.route('/publishers.json')
def publishers_json():
    page_size = 20

    search = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    show_errors = request.args.get('errors', False) == 'true'

    if show_errors:
        publishers = (
            db.session.query(
                models.Publisher,
                db.func.COUNT(models.DownloadError.id)
                .op("+")(db.func.COUNT(models.XMLError.id))
                .label('total'))
            .select_from(models.Publisher)
            .outerjoin(models.DownloadError)
            .outerjoin(models.XMLError)
            .filter((models.Publisher.name.ilike(f'%{search}%')) |
                    (models.Publisher.id.ilike(f'%{search}%')))
            .group_by(models.Publisher.id)
            .order_by(db.desc(db.text('total')), models.Publisher.name)
            .paginate(page, page_size)
        )
        results = [{
            'id': p.id,
            'text': p.name,
            'error_count': count,
        } for p, count in publishers.items]
    else:
        publishers = (models.Publisher.query
                      .filter((models.Publisher.name.ilike(f'%{search}%')) |
                              (models.Publisher.id.ilike(f'%{search}%')))
                      .order_by(models.Publisher.name)
                      .paginate(page, page_size)
                      )
        results = [{
            'id': p.id,
            'text': p.name,
        } for p in publishers.items]

    return jsonify({
        'results': results,
        'pagination': {
            'more': publishers.has_next
        }
    })


@blueprint.route('/publisher/<publisher_id>')
def publisher(publisher_id):
    try:
        publisher = models.Publisher.find_or_fail(publisher_id)
    except ModelNotFoundError:
        return abort(404)
    errors = publisher.download_errors + publisher.xml_errors + \
        publisher.validation_errors
    return render_template('publisher.html',
                           publisher=publisher,
                           errors=errors)
