from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    website_url = db.Column(db.String(150))
    website_application_password = db.Column(db.String(150))
    membership_level = db.Column(db.String(150))
    has_paid = db.Column(db.Boolean, default=False)
