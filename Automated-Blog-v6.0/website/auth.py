from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail
from flask_login import login_user, login_required, logout_user, current_user
import config
import stripe
from .models import Member
import pyotp
from flask_mail import Message
import datetime

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

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        user = User.query.filter_by(email=email).first()
        
        if user:
            sendVerifcationEmail(user, email)

            flash('Password reset email sent!', category='success')
            return redirect(url_for('auth.enter_verification', id=user.id))
        else:
            flash('Email does not exist.', category='error')
            return render_template("forgotPassword.html", user=current_user)

    return render_template("forgotPassword.html", user=current_user)

@auth.route('/enter-verification', methods=['GET', 'POST'])
def enter_verification():
    if request.method == 'POST':
        id = request.args.get('id', '')
        if 'code' in request.form:
            code = request.form.get('code')
            user_id = User.query.filter_by(id=id).first()
            db.session.commit()


            if user_id == None: 
                return redirect(url_for('auth.login'))
            elif user_id.user_reset_submissions < 3 or (datetime.datetime.now() - user_id.user_last_reset_submission).total_seconds() > 60:
                user_id.user_last_reset_submission = datetime.datetime.now()
                db.session.commit()

                user_token = User.query.filter_by(token=code).first()

                if user_token:
                    user_id.user_reset_submissions = 0
                    user_id.user_last_reset_submission = datetime.datetime.now()
                    db.session.commit()
                    flash('Correct Code', category='success')
                    return render_template("enterVerification.html", user=current_user, correct_code=True, id=user_id.id)
                else:
                    user_id.user_reset_submissions = user_id.user_reset_submissions + 1
                    db.session.commit()
                    flash('Incorrect Code', category='error')
                    return render_template("enterVerification.html", user=current_user, correct_code=False, id=user_id.id)
            else:
                flash('Too many attempts, please wait 60 seconds.', category='error')
                return render_template("enterVerification.html", user=current_user, correct_code=False, id=user_id.id)



        elif 'password1' in request.form:
            id = request.form.get('id') 
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            if password1 != password2:
                flash('Passwords don\'t match.', category='error')
                return render_template("enterVerification.html", user=current_user, correct_code=True, id=id)
            elif len(password1) < 7:
                flash('Password must be at least 7 characters.', category='error')
                return render_template("enterVerification.html", user=current_user, correct_code=True, id=id)
            else:
                user = User.query.filter_by(id=id).first()
                print(user)
                user.password = generate_password_hash(password1, method='sha256')
                user.token = ''
                db.session.commit()

                flash('Password reset successfully!', category='success')
                return redirect(url_for('auth.login'))

    return render_template("enterVerification.html", user=current_user, correct_code=False)


    


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



def sendVerifcationEmail(user, email):
    key = pyotp.random_base32()
    token = pyotp.TOTP(key).now()
    user.token = token
    db.session.commit()

    message = Message(
        'Password Reset',
        sender='noreply@demo.com',
        recipients=[email],
        body=f'Verification code is {token}'
    )
    mail.send(message)
