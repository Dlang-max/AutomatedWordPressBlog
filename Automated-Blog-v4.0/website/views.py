from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Blog
from .models import Member
from . import db
import json
import BlogWriter
import config
import stripe

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)

@views.route('/base', methods=['GET', 'POST'])
def base():
    return render_template("base.html", user=current_user)

@views.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    email = current_user.email
    member = Member.query.filter_by(email=email).first()
    if member:
        subscription_id = member.subscription_id
        

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            print(subscription)

            membership_level = config.prices[subscription['items']['data'][0]['plan']['id']]
        except stripe.error.StripeError as e:
            print(':(')
        
        current_user.subscription_id = subscription_id
        current_user.membership_level = membership_level
        current_user.blogs_remaining_this_month = config.blogs_with_membership[membership_level]
        current_user.has_paid = True
        db.session.commit()

        member_to_delete = Member.query.filter_by(email=email).first()
        db.session.delete(member_to_delete)
        db.session.commit()

    return render_template("dashboard.html", user=current_user) 

@views.route('/generate-blog', methods=['GET', 'POST'])
@login_required
def generateBlog():
    content = ''
    title = ''

    if request.method == 'POST':
        title = request.form.get('blog-title')
        additional_information = request.form.get('additional-information')

        outline = BlogWriter.BlogWriter.writeBlogOutline(title=title)
        content = BlogWriter.BlogWriter.writeBlog(title=title, outline=outline, additional_information=additional_information)          

        # new_blog = Blog(blog_title=title, blog_content=content)
        # db.session.add(new_blog)
        # db.session.commit()

        # current_user.free_blogs_remaining = 0


        # if current_user.free_blogs_remaining == 0:
        #     current_user.blogs_remaining_this_month -= 1

        # db.session.commit()



    return render_template("generate_blog.html", user=current_user, title=title, content=content)

# def getMembershipLevel(subscription_id):
#     try:
#         subscription = stripe.Subscription.retrieve()
#         price_id = subscription['data'][0]['plan']['id']
#     except stripe.error.StripeError as e:
#         print(f"Error: {e}")
#         return None
#     return config.prices['']

