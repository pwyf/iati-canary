from os.path import abspath, dirname

from environs import Env


basedir = abspath(dirname(__file__))

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'

SQLALCHEMY_DATABASE_URI = env.str('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = env.str('SECRET_KEY')

MAILGUN_DOMAIN = env.str('MAILGUN_DOMAIN')
MAILGUN_API_KEY = env.str('MAILGUN_API_KEY')
