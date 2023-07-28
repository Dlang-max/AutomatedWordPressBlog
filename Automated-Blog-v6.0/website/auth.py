from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
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
                return redirect(url_for('views.generateBlog'))
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
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')



        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        
        else:
            new_user = User(email=email, password=generate_password_hash(
                password1, method='sha256'))
            

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.generateBlog'))

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

@auth.route('/cancelMembership', methods=['GET', 'POST'])
@login_required
def cancelMembership():
    stripe.api_key = config.stripe_keys["secret_key"]
    stripe.Subscription.delete(current_user.subscription_id)




    current_user.subscription_id = ''
    current_user.membership_level = 'Free'
    db.session.commit()

    return render_template("profile.html", user=current_user)

@auth.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    price = request.form.get('priceId')
    domain_url = 'http://localhost:5000/'
    stripe.api_key = config.stripe_keys["secret_key"]


    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + '/generate-blog',
            cancel_url=domain_url + '/generate-blog',
            mode='subscription',
            line_items=[{
                'price': price,
                'quantity': 1
            }],
        )

        current_user.stripe_id = checkout_session['id']
        db.session.commit()
        print(current_user.stripe_id)

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

    if event["type"] == "checkout.session.completed":
        subscription_id = event['data']['object']['subscription']
        member_emial = event['data']['object']['customer_details']['email']
        stripe_id = event['data']['object']['id']




        member_to_delete = Member.query.filter_by(stripe_id=stripe_id).first()

        if member_to_delete:
            stripe.Subscription.delete(member_to_delete.subscription_id)
            db.session.delete(member_to_delete)
            db.session.commit()

        new_member = Member(email=member_emial, subscription_id=subscription_id, stripe_id=stripe_id)
        db.session.add(new_member)
        db.session.commit()

    return redirect(url_for('views.generateBlog'))