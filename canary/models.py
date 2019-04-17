from functools import reduce
from datetime import datetime, timedelta

from flask import current_app, render_template
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from .extensions import db, mail
from sqlalchemy_mixins import AllFeaturesMixin


class CreatedUpdatedMixin(object):
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow,
                            onupdate=datetime.utcnow)


class BaseModel(db.Model, AllFeaturesMixin):
    __abstract__ = True


class Publisher(BaseModel, CreatedUpdatedMixin):
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    total_datasets = db.Column(db.Integer, default=0, nullable=False)
    first_published_on = db.Column(db.Date)


class Contact(BaseModel, CreatedUpdatedMixin):
    __table_args__ = (db.UniqueConstraint('email', 'publisher_id'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=True)
    publisher = db.relationship('Publisher',
                                backref=db.backref('contacts', lazy=True))
    active = db.Column(db.Boolean, default=False, nullable=False)
    confirmed_at = db.Column(db.DateTime)
    last_messaged_at = db.Column(db.DateTime)

    @classmethod
    def _get_serializer(cls):
        return URLSafeTimedSerializer(
            secret_key=current_app.config.get('SECRET_KEY'),
            salt=current_app.config.get('SECURITY_RESET_SALT', 'reset-salt'))

    def generate_token(self):
        serializer = self._get_serializer()
        return serializer.dumps([self.id, None])

    @classmethod
    def load_token(cls, token, max_days_old=7):
        serializer = cls._get_serializer()
        max_age = timedelta(days=max_days_old).total_seconds()
        contact, data = None, None
        expired, invalid = False, False
        try:
            data = serializer.loads(token, max_age=max_age)
        except SignatureExpired:
            d, data = serializer.loads_unsafe(token)
            expired = True
        except (BadSignature, TypeError, ValueError):
            invalid = True

        if data:
            contact = cls.find(data[0])

        expired = expired and (contact is not None)
        invalid = invalid or (contact is None)

        return expired, invalid, contact

    def send_email_confirmation(self):
        token = self.generate_token()
        text = render_template('emails/confirm_email.txt', token=token)
        html = render_template('emails/confirm_email.html', token=token)
        mail.send_message(
            subject='Please confirm your email address',
            sender='IATI-Canary <no-reply@iati-canary.org>',
            recipients=[f'{self.name} <{self.email}>'],
            body=text,
            html=html,
        )
        self.last_messaged_at = datetime.utcnow()
        self.save()

    def send_email_alert(self, level='warning'):
        errors = {
            'validation': [],
            'download': self.publisher.download_errors(
                currently_erroring=True),
            'xml': self.publisher.xml_errors(
                currently_erroring=True),
        }
        if level == 'info':
            errors['validation'] = self.publisher.validation_errors(
                currently_erroring=True)
        if reduce(lambda x, y: x + y, errors.values()) == []:
            return

        # token = self.generate_token()

        # text = render_template(f'emails/{level}.txt',
        #     errors=errors, token=token)
        # html = render_template(f'emails/{level}.html',
        #     errors=errors, token=token)

        # if level == 'info':
        #     subject = 'Some datasets have issues'
        # else:
        #     subject = 'Warning: Some datasets are broken'

        # mail.send_message(
        #     subject=subject,
        #     sender='IATI-Canary <no-reply@iati-canary.org>',
        #     recipients=[f'{self.name} <{self.email}>'],
        #     body=text,
        #     html=html,
        # )
        # self.last_messaged_at = datetime.utcnow()
        # self.save()


class DatasetError(BaseModel, CreatedUpdatedMixin):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(255), unique=True, nullable=False)
    dataset_name = db.Column(db.Text)
    dataset_url = db.Column(db.String(255), nullable=False)
    currently_erroring = db.Column(db.Boolean, default=True, nullable=False)
    error_count = db.Column(db.Integer, default=1, nullable=False)
    check_count = db.Column(db.Integer, default=1, nullable=False)
    last_errored_at = db.Column(db.DateTime, nullable=False,
                                default=datetime.utcnow)


class DownloadError(DatasetError):
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=False)
    publisher = db.relationship('Publisher',
                                backref=db.backref('download_errors',
                                                   lazy=True))


class XMLError(DatasetError):
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=False)
    publisher = db.relationship('Publisher',
                                backref=db.backref('xml_errors',
                                                   lazy=True))


class ValidationError(DatasetError):
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=False)
    publisher = db.relationship('Publisher',
                                backref=db.backref('validation_errors',
                                                   lazy=True))
