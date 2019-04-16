from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email
from sqlalchemy_mixins import ModelNotFoundError

from . import models


class DynamicSelectField(SelectField):
    def pre_validate(self, form):
        try:
            pub = models.Publisher.find_or_fail(self.data)
            self.choices = [(pub.id, pub.name)]
        except ModelNotFoundError:
            raise ValueError(self.gettext('Please choose a publisher.'))


class UniqueEmailField(StringField):
    def pre_validate(self, form):
        pub = models.Contact.where(
            email=self.data,
            publisher_id=form.data['publisher_id'],
        ).first()
        if pub:
            msg = 'That email address is signed up for that publisher.'
            raise ValueError(self.gettext(msg))


class SignupForm(FlaskForm):
    render_kw = {'class': 'form-control form-control-lg'}
    name = StringField('Name', render_kw=render_kw, validators=[
        DataRequired('Please enter your name.')])
    email = UniqueEmailField('Email Address', render_kw=render_kw, validators=[
        DataRequired('Please enter your email address.'),
        Email('Please enter a valid email address.')])
    publisher_id = DynamicSelectField('Publisher', render_kw=render_kw,
                                      choices=[], id='select-publisher')
    submit = SubmitField('Sign up')
