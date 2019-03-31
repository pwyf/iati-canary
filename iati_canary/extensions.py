from flask_cachebuster import CacheBuster
from playhouse.flask_utils import FlaskDB


db = FlaskDB()
cache_buster = CacheBuster()
