from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email
from sqlalchemy_mixins import ModelNotFoundError

from . import models


class DynamicSelectField(SelectField):
    def pre_validate(self, form):
        try:
            pub = models.Publisher.find_or_fail(form.publisher.data)
            form.publisher.choices = [(pub.id, pub.name)]
        except ModelNotFoundError:
            raise ValueError(self.gettext('Please choose a publisher.'))


class SignupForm(FlaskForm):
    render_kw = {'class': 'form-control form-control-lg'}
    name = StringField('Name', render_kw=render_kw, validators=[
        DataRequired('Please enter your name.')])
    email = StringField('Email Address', render_kw=render_kw, validators=[
        DataRequired('Please enter your email address.'),
        Email('Please enter a valid email address.')])
    publisher = DynamicSelectField('Publisher', render_kw=render_kw,
                                   choices=[], id='select-publisher')
    submit = SubmitField('Sign up')
