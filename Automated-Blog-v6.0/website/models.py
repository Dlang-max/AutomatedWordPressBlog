from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func




class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(150))
    blog_content = db.Column(db.String(20000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    subscription_id = db.Column(db.String(150), unique=True)
    stripe_id = db.Column(db.String(150), unique=True)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    website_url = db.Column(db.String(150), default='')
    website_username = db.Column(db.String(150))
    website_application_password = db.Column(db.String(150))
    membership_level = db.Column(db.String(150), default='Free')
    free_blogs_remaining = db.Column(db.Integer, default=1)
    blogs_remaining_this_month = db.Column(db.Integer, default=0)
    subscription_id = db.Column(db.String(150))
    has_paid = db.Column(db.Boolean, default=False)
    stripe_id = db.Column(db.String(150), unique=True)
    blogs = db.db.relationship('Blog')

    # def get_reset_token(self, expires_sec=1800):
    #     s = Serializer(app.config.SECRET_KEY, expires_sec)
    #     return s.dumps({'user_id': self.id}).decode('utf-8')


