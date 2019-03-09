from os.path import abspath, dirname

from environs import Env


basedir = abspath(dirname(__file__))

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'

DATABASE = {
    'name': env.str('FLASK_DB_NAME', default='canary'),
    'engine': 'peewee.PostgresqlDatabase',
    'user': env.str('FLASK_DB_USER', default=None),
    # 'max_connections': 32,
    # 'stale_timeout': 600,
    'password': env.str('FLASK_DB_PASSWORD', default=None),
    'host': env.str('FLASK_DB_HOST', default=None),
    'port': env.str('FLASK_DB_PORT', default=None),
}
