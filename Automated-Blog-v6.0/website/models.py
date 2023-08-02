from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func




class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(150), default='')
    blog_content = db.Column(db.String(20000), default='')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_url = db.Column(db.String(150), default='')
    image = db.Column(db.LargeBinary)

class WrittenBlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_title = db.Column(db.String(150), default='')
    blog_content = db.Column(db.Text(), default='')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_url = db.Column(db.String(150), default='')
    image = db.Column(db.LargeBinary)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150))
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
    token = db.Column(db.String(150))
    unique_token = db.Column(db.String(150), unique=True)

    user_reset_submissions = db.Column(db.Integer(), default=0)
    user_last_reset_submission = db.Column(db.DateTime())

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150)) 




