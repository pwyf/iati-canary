from flask_cachebuster import CacheBuster
from playhouse.flask_utils import FlaskDB
from flask_mailgun import MailGun


db = FlaskDB()
cache_buster = CacheBuster()
mail = MailGun()
