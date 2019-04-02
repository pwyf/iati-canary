from os.path import abspath, dirname

from environs import Env


basedir = abspath(dirname(__file__))

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'

DATABASE = env.str('DATABASE_URL')

SECRET_KEY = env.str('SECRET_KEY')
