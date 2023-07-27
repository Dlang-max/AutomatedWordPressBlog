from flask import Blueprint, render_template, request, flash, jsonify, session
from flask_login import login_required, current_user
from .models import Blog
from .models import Member
from . import db
import json
import BlogWriter
import config
import stripe
import base64
import requests

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("base.html", user=current_user)

@views.route('/base', methods=['GET', 'POST'])
def base():
    return render_template("base.html", user=current_user)

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@views.route('/generate-blog', methods=['GET', 'POST'])
@login_required
def generateBlog():
    stripe_id = current_user.stripe_id
    member = Member.query.filter_by(stripe_id=stripe_id).first()
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
        current_user.blogs_remaining_this_month = current_user.blogs_remaining_this_month + config.blogs_with_membership[membership_level]
        current_user.has_paid = True
        db.session.commit()

        member_to_delete = Member.query.filter_by(stripe_id=stripe_id).first()
        db.session.delete(member_to_delete)
        db.session.commit()

    if request.method == 'POST':
        if 'blog-title' in request.form :
            title = request.form.get('blog-title')
            additional_information = request.form.get('additional-information')

            outline = BlogWriter.BlogWriter.writeBlogOutline(title=title)
            content = BlogWriter.BlogWriter.writeBlog(title=title, outline=outline, additional_information=additional_information)
            image_url = getImages(BlogWriter.BlogWriter.getSubject(title=title))

            if image_url != None:
                content = f'<img src="{getImages(BlogWriter.BlogWriter.getSubject(title=title))}" alt="blog image" width="100%" height="auto" /> \n' + content

            new_blog = Blog(blog_title=title, blog_content=content, user_id=current_user.id)
            db.session.add(new_blog)
            db.session.commit()

            if current_user.free_blogs_remaining == 0:
                current_user.blogs_remaining_this_month -= 1

            current_user.free_blogs_remaining = 0
            
            db.session.commit()  
  



            return render_template("generate_blog.html", generating=True, generate=True, user=current_user, title=title, content=content, wants_to_link_wordpress=False)


        if 'div_content' in request.form:
            if current_user.website_url == '':

                blog = Blog.query.filter_by(user_id=current_user.id).first()
                print(blog.blog_content)
                print(current_user.id)
                print(blog)

                blog.blog_content = request.form.get('div_content')
                db.session.commit()

                return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)
            
            url = str(current_user.website_url) + '/wp-json/wp/v2/posts'

            user = current_user.website_username
            password = current_user.website_application_password

            creds = user + ':' + password

            token = base64.b64encode(creds.encode())

            header = {'Authorization': 'Basic ' + token.decode('utf-8')}

            blog = Blog.query.filter_by(user_id=current_user.id).first()
            blog.blog_content = request.form.get('div_content')
            db.session.commit()

            print('content: ' + request.form.get('div_content'))



            post = {
                'title': blog.blog_title,
                'content': blog.blog_content,
                'status': 'publish'
            }

            r = requests.post(url, headers=header, json=post)
            print(r)


            db.session.delete(blog)
            db.session.commit()

            return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)


        if 'websiteURL' in request.form:
            website_url = request.form.get('websiteURL')
            website_username = request.form.get('wordPressUsername')
            website_application_password = request.form.get('appPassword1')

            current_user.website_url = website_url
            current_user.website_username = website_username
            current_user.website_application_password = website_application_password
            db.session.commit()   

            blog = Blog.query.filter_by(user_id=current_user.id).first()


            return render_template("generate_blog.html", generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=False)

    return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)


def getImages(query):

    query = query.replace(' ', '+')
    url = f'https://pixabay.com/api/?key={config.pixabay_api_key}&q={query}&image_type=photo'

    response = requests.get(url)
    data = response.json()

    if data['hits']:
        return data['hits'][0]['webformatURL']
    return None



