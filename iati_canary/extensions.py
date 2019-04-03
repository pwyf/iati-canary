from flask_cachebuster import CacheBuster
from playhouse.flask_utils import FlaskDB
from flask_sendgrid import SendGrid


db = FlaskDB()
cache_buster = CacheBuster()
mail = SendGrid()
