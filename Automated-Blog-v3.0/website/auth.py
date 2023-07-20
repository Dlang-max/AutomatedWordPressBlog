from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import config
import stripe


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
                password1, method='sha256'), website_url=website_url, 
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
def create_checkout_session():
    price = request.form.get('priceId')
    domain_url = 'http://localhost:5000/'
    stripe.api_key = config.stripe_keys["secret_key"]


    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [customer_email] - lets you prefill the email input in the form
        # [automatic_tax] - to automatically calculate sales tax, VAT and GST in the checkout page
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + '/',
            cancel_url=domain_url + '/',
            mode='subscription',
            # automatic_tax={'enabled': True},
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
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")
        print(event['data']['object']['subscription'])
        global subscription_confirmed 
        subscription_confirmed = True
        print(subscription_confirmed)
        
    return redirect(url_for('views.dashboard'))