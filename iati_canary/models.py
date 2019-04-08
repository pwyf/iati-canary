from datetime import datetime

from .extensions import db
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
    last_checked_at = db.Column(db.DateTime)
    queued_at = db.Column(db.DateTime, default=datetime.utcnow)


class Contact(BaseModel, CreatedUpdatedMixin):
    __table_args__ = (db.UniqueConstraint('email', 'publisher_id'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=False)
    publisher = db.relationship('Publisher',
                                backref=db.backref('contacts', lazy=True))
    active = db.Column(db.Boolean, default=True, nullable=False)
    confirmed_at = db.Column(db.DateTime)
    last_messaged_at = db.Column(db.DateTime)


class DatasetError(BaseModel, CreatedUpdatedMixin):
    __tablename__ = 'dataseterror'
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(255), unique=True, nullable=False)
    dataset_name = db.Column(db.Text, nullable=False)
    dataset_url = db.Column(db.String(255), nullable=False)
    publisher_id = db.Column(db.String(255),
                             db.ForeignKey('publisher.id', ondelete='CASCADE'),
                             nullable=False)
    publisher = db.relationship('Publisher',
                                backref=db.backref('errors', lazy=True))
    error_type = db.Column(db.String(20))
    last_status = db.Column(db.String(20), default='fail', nullable=False)
    error_count = db.Column(db.Integer, default=1, nullable=False)
    check_count = db.Column(db.Integer, default=1, nullable=False)
    last_errored_at = db.Column(db.DateTime, nullable=False,
                                default=datetime.utcnow)

    @classmethod
    def upsert(cls, success, **kwargs):
        dataset_error = cls.where(dataset_id=kwargs.get('dataset_id')).first()
        if not dataset_error:
            if success:
                return
            return cls.create(**kwargs)
        dataset_error.check_count += 1
        if success:
            dataset_error.last_status = 'success'
            return dataset_error.save()
        dataset_error.last_status = 'fail'
        if dataset_error.error_type != kwargs.get('error_type') and \
                kwargs.get('error_type') == 'schema':
            # delete old error and replace
            dataset_error.delete()
            return cls.create(**kwargs)
        dataset_error.last_errored_at = datetime.now()
        dataset_error.error_count += 1
        return dataset_error.save()
