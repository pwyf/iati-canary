from datetime import datetime
from os.path import join

from flask import abort, Blueprint, render_template, send_from_directory, \
                  jsonify, request, redirect, url_for, flash
from sqlalchemy_mixins import ModelNotFoundError

from . import models, utils
from .extensions import db
from .forms import SignupForm


blueprint = Blueprint('canary', __name__,
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
        models.Contact.create(
            name=form.data['name'],
            email=form.data['email'],
            publisher_id=form.data['publisher_id'],
        )
        flash('Thanks! You’ll receive a confirmation email ' +
              'shortly.', 'success')
        return redirect(url_for('canary.home') + '#sign-up')

    numbers = utils.get_stats()
    return render_template(
        'home.html',
        numbers=numbers,
        form=form,
    )


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
            .outerjoin(models.DownloadError,
                       db.and_(
                           models.DownloadError.publisher_id == models.Publisher.id,
                           models.DownloadError.currently_erroring.is_(True)))
            .outerjoin(models.XMLError,
                       db.and_(
                           models.XMLError.publisher_id == models.Publisher.id,
                           models.XMLError.currently_erroring.is_(True)))
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
    error_dict = {}
    all_errors = {
        '_download': publisher.download_errors,
        '_xml': publisher.xml_errors,
        'validation': publisher.validation_errors
    }
    for err_type, errors in all_errors.items():
        for error in errors:
            if error.dataset_id not in error_dict:
                error_dict[error.dataset_id] = (err_type, error)
                continue
            if error_dict[error.dataset_id][1].currently_erroring:
                continue
            error_dict[error.dataset_id] = (err_type, error)
    errors = sorted(list(error_dict.values()),
                    key=lambda x: (x[1].currently_erroring is False, x[0]))
    broken_count = len([e for e in errors
                        if e[1].currently_erroring
                        and e[0] != 'validation'])
    validation_count = len([e for e in errors
                            if e[1].currently_erroring and
                            e[0] == 'validation'])

    return render_template('publisher.html',
                           publisher=publisher,
                           errors=errors,
                           broken_count=broken_count,
                           validation_count=validation_count)


@blueprint.route('/publisher/badge/<publisher_id>.json')
def publisher_badge_json(publisher_id):
    try:
        publisher = models.Publisher.find_or_fail(publisher_id)
    except ModelNotFoundError:
        return abort(404)

    if publisher.download_errors == [] and publisher.xml_errors == []:
        status = 'success'
        message = 'passing'
        is_error = False
    else:
        status = 'critical'
        message = 'errors'
        is_error = True


    return jsonify({
        'schemaVersion': 1,
        'label': 'canary',
        'message': message,
        'color': status,
        'isError': is_error,
    })


@blueprint.route('/confirm/<token>')
def confirm_email(token):
    expired, invalid, contact = models.Contact.load_token(token)
    if invalid:
        flash('Oops! Something went wrong – we were not able to ' +
              'subscribe you. Please try again.', 'danger')
    elif expired:
        flash('Oops! That link has expired – we were not able to ' +
              'subscribe you. Please try again.', 'danger')
    else:
        contact.active = True
        contact.confirmed_at = datetime.utcnow()
        contact.save()
        flash('Success! You’re subscribed to email updates.',
              'success')
    return redirect(url_for('canary.home') + '#sign-up')


@blueprint.route('/unsubscribe/<token>')
def unsubscribe(token):
    _, invalid, contact = models.Contact.load_token(token)
    if invalid:
        flash('Oops! Something went wrong – we were not able to ' +
              'unsubscribe you. Please try again.', 'danger')
    else:
        contact.active = False
        contact.save()
        flash('You were successfully unsubscribed.',
              'success')
    return redirect(url_for('canary.home') + '#sign-up')
