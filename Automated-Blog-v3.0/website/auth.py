from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import config
import stripe
from .models import Member



auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        website_username = request.form.get('wordPressUsername')
        website_url = request.form.get('websiteURL')
        app_pass_1 = request.form.get('appPassword1')
        app_pass_2 = request.form.get('appPassword2')
        subscription_type = 'Free'



        user = User.query.filter_by(email=email).first()
        website = User.query.filter_by(website_url=website_url).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif website:
            flash('Website URL already being used.', category='error')
        elif len(website_url) < 1:
            flash('Website URL must be at least 1 character.', category='error')
        elif app_pass_1 != app_pass_2:
            flash('Application passwords don\'t match.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'), website_url=website_url, website_username=website_username,
                website_application_password=generate_password_hash(app_pass_1, method='sha256'),
                membership_level=subscription_type)
            

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.dashboard'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/config')
@login_required
def get_publishable_key():
    stripe_config = {'publicKey': config.stripe_keys['publishable_key']}
    return jsonify(stripe_config)



@auth.route('/upgradeMembership', methods=['GET', 'POST'])
@login_required
def upgradeMembership():
    return render_template("upgradeMembership.html", user=current_user)


@auth.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    price = request.form.get('priceId')
    domain_url = 'http://localhost:5000/'
    stripe.api_key = config.stripe_keys["secret_key"]


    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + '/dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + '/dashboard',
            mode='subscription',
            line_items=[{
                'price': price,
                'quantity': 1
            }],
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@auth.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        return "Invalid signature", 400

    print(event['type'])
    if event["type"] == "checkout.session.completed":
        subscription_id = event['data']['object']['subscription']
        member_emial = event['data']['object']['customer_details']['email']



        member_to_delete = Member.query.filter_by(email=member_emial).first()

        if member_to_delete:
            db.session.delete(member_to_delete)
            db.session.commit()

        new_member = Member(email=member_emial, subscription_id=subscription_id)
        db.session.add(new_member)
        db.session.commit()

    return redirect(url_for('views.dashboard'))