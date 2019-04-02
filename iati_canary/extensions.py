from flask_cachebuster import CacheBuster
from playhouse.flask_utils import FlaskDB
from flask_mail import Mail


db = FlaskDB()
cache_buster = CacheBuster()
mail = Mail()
