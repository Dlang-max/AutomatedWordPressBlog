from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from .utils import make_celery
from celery.schedules import crontab
import os

db = SQLAlchemy()
DB_NAME = "database.db"
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'langd052405@gmail.com'
    app.config['MAIL_PASSWORD'] = os.environ.get('email_password')
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config["CELERY_CONFIG"] = {"broker_url": "redis://localhost:6379/0", "result_backend": "redis://localhost:6379/0",
        "beat_schedule" : {
            "check-members-every-month":{
                "task": 'website.tasks.check_members',
                "schedule":  crontab(0, 0, day_of_month='1'),
            }
        }}




    mail.init_app(app)


    csrf = CSRFProtect(app)


    from website.auth import stripe_webhook

    csrf.exempt(stripe_webhook)
    # Local Database
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://strfhblwizdajz:1cb9c3fac484d0e956556dd679e91fd24c39e9c6120bf7abd65b21ae98d4458a@ec2-34-236-103-63.compute-1.amazonaws.com:5432/d8ao5eev9u89qg'

    db.init_app(app) 

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    celery = make_celery(app)
    celery.set_default()

    from .models import User
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)



    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app, celery


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')

