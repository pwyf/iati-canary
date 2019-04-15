from flask_cachebuster import CacheBuster
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mailgun import MailGun


db = SQLAlchemy(session_options={
        "autocommit": True,
        "autoflush": False,
        "expire_on_commit": False,
    })
migrate = Migrate()
cache_buster = CacheBuster()
mail = MailGun()
