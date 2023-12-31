from flask import Blueprint, render_template, request, flash, jsonify, session
from flask_login import login_required, current_user
from .models import Blog
from .models import Member
from .models import WrittenBlog
from . import db
import json
import BlogWriter
import stripe
import base64
import requests
import openai
import os
from .tasks import add_blog
from .info import prices, blogs_with_membership



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
    check_stripe_membership(current_user)

    
    if request.method == 'POST':
        if 'blog-title' in request.form :
            title = request.form.get('blog-title')
            additional_information = request.form.get('additional-information')

            if title == '':
                flash('Please enter a title for your blog.', category='error')
                return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)


            task = add_blog.delay(title, additional_information, current_user.id)

            # Remove a blog from the user's remaining blogs
            if current_user.free_blogs_remaining == 0:
                current_user.blogs_remaining_this_month -= 1
            current_user.free_blogs_remaining = 0
            db.session.commit()  
  
            flash('Blog Generating', category='success')
            return render_template("generate_blog.html", generating=True, generate=True, user=current_user, title=title, content='', wants_to_link_wordpress=False)

        if 'websiteURL' in request.form:
            website_url = request.form.get('websiteURL')
            website_username = request.form.get('wordPressUsername')
            website_application_password_1 = request.form.get('appPassword1')
            website_application_password_2 = request.form.get('appPassword2')

            blog = Blog.query.filter_by(user_id=current_user.id).first()


            if website_application_password_1 != website_application_password_2:
                flash('Application Passwords do not match.', category='error')
                return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)


            current_user.website_url = website_url
            current_user.website_username = website_username
            current_user.website_application_password = website_application_password_1
            db.session.commit()   


            flash('Linked to WordPress!', category='success')
            return render_template("generate_blog.html", generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=False)

        if 'no-thanks' in request.form:
            blog = Blog.query.filter_by(user_id=current_user.id).first()
            db.session.delete(blog)
            db.session.commit()
            flash('Blog Deleted', category='success')
            return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)

        if 'div_content' in request.form:
            if current_user.website_url == '':
                blog = Blog.query.filter_by(user_id=current_user.id).first()
                blog.blog_content = request.form.get('div_content')
                db.session.commit()

                return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)
            
            post_url = str(current_user.website_url) + '/wp-json/wp/v2/posts'
            media_url = str(current_user.website_url) + '/wp-json/wp/v2/media'

            user = current_user.website_username
            password = current_user.website_application_password

            creds = user + ':' + password

            token = base64.b64encode(creds.encode())

            header = {'Authorization': 'Basic ' + token.decode('utf-8')}

            blog = Blog.query.filter_by(user_id=current_user.id).first()
            blog.blog_content = request.form.get('div_content')
            db.session.commit()

            post = {
                'title': blog.blog_title,
                'content': blog.blog_content,
                'status': 'publish'
            }

            if blog.image_url != '':
                image_data = requests.get(blog.image_url).content

                media = {
                    'file': (blog.image_url, image_data, 'image/png'),
                    'status': 'publish'
                }

            try: 
                post_request = requests.post(post_url, headers=header, json=post)
                post_id = post_request.json().get('id')

                if blog.image_url != '':
                    media_request = requests.post(media_url, headers=header, files=media)
                    media_id = media_request.json().get('id')

                    featured_payload = {
                        'featured_media': media_id
                    }

                    update_request = requests.post(post_url + '/' + str(post_id), headers=header, json=featured_payload)


                if post_request.status_code or update_request == 201:
                    db.session.delete(blog)
                    db.session.commit()
                flash('Blog Posted to WordPress!', category='success')
            except requests.exceptions.ConnectionError:
                flash('Error connecting to WordPress. Please check your URL and try again.', category='error')
                return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)
            
    
            if check_if_user_has_blog(current_user):
                blog = Blog.query.filter_by(user_id=current_user.id).first()
                return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=False)
            return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)


        
        
        
    if check_if_user_has_blog(current_user):
        print('here')
        blog = Blog.query.filter_by(user_id=current_user.id).first()
        return render_template("generate_blog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=False)


    return render_template("generate_blog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)



@views.route('/writeBlog', methods=['GET', 'POST'])
@login_required
def writeBlog():
    if request.method == 'POST':

        if 'blog-title' in request.form:
            title = request.form.get('blog-title')
            content = request.form.get('div_content')
            image = request.form.get('file')

            if title == '':
                flash('Please enter a title for your blog.', category='error')
                return render_template("writeBlog.html", user=current_user, title='', content=content, wants_to_link_wordpress=False)

            if content == '':
                flash('Please enter content for your blog.', category='error')
                return render_template("writeBlog.html", user=current_user, title=title, content='', wants_to_link_wordpress=False)
            
            
            new_written_blog = WrittenBlog(blog_title=title, blog_content=content, user_id=current_user.id)
            db.session.add(new_written_blog)
            db.session.commit()

            if current_user.website_url == '':
                flash('Link to WordPress to post your blog.', category='error')
                return render_template("writeBlog.html", user=current_user, title=new_written_blog.blog_title, content=new_written_blog.blog_content, wants_to_link_wordpress=True)


            if current_user.free_blogs_remaining == 0:
                current_user.blogs_remaining_this_month -= 1

            current_user.free_blogs_remaining = 0
            db.session.commit()  

            url = str(current_user.website_url) + '/wp-json/wp/v2/posts'

            user = current_user.website_username
            password = current_user.website_application_password

            creds = user + ':' + password

            token = base64.b64encode(creds.encode())

            header = {'Authorization': 'Basic ' + token.decode('utf-8')}

            blog = WrittenBlog.query.filter_by(user_id=current_user.id).first()
            blog.blog_content = request.form.get('div_content')
            db.session.commit()




            post = {
                'title': blog.blog_title,
                'content': blog.blog_content,
                'status': 'publish'
            }

            try: 
                r = requests.post(url, headers=header, json=post)
            except requests.exceptions.ConnectionError:
                flash('Error connecting to WordPress. Please check your URL and try again.', category='error')
                return render_template("writeBlog.html", generating=False, generate=True, user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)


            blog = WrittenBlog.query.filter_by(user_id=current_user.id).first()
            db.session.delete(blog)
            db.session.commit()

            flash('Blog Posted to WordPress!', category='success')

            return render_template("writeBlog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)
        
        elif 'wordPressUsername' in request.form:
            website_url = request.form.get('websiteURL')
            website_username = request.form.get('wordPressUsername')
            website_application_password_1 = request.form.get('appPassword1')
            website_application_password_2 = request.form.get('appPassword2')

            blog = WrittenBlog.query.filter_by(user_id=current_user.id).first()


            if website_application_password_1 != website_application_password_2:
                flash('Application Passwords do not match.', category='error')
                return render_template("writeBlog.html", user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=True)

            current_user.website_url = website_url
            current_user.website_username = website_username
            current_user.website_application_password = website_application_password_1
            db.session.commit()  


            flash('Linked to WordPress!', category='success')
            return render_template("writeBlog.html", user=current_user, title=blog.blog_title, content=blog.blog_content, wants_to_link_wordpress=False)
        
    return render_template("writeBlog.html", generating=False, generate=False, user=current_user, title='', content='', wants_to_link_wordpress=False)


"""
Gets an image from Pixabay based on the title of the blog.

Parameters:
    query (string): The title of the blog.
Returns:
    string: The URL of the image.
"""
def get_images(query):

    query = query.replace(' ', '+')
    url = f'https://pixabay.com/api/?key={os.environ.get("pixabay_api_key")}&q={query}&image_type=photo'

    response = requests.get(url)
    data = response.json()

    if data['hits']:
        return data['hits'][0]['webformatURL']
    return None
"""
Checks if the user is a new member. If so, it adds the user to the database.
"""
def check_stripe_membership(current_user):
    stripe_id = current_user.stripe_id
    member = Member.query.filter_by(stripe_id=stripe_id).first()
    if member:
        subscription_id = member.subscription_id
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            membership_level = info.prices[subscription['items']['data'][0]['plan']['id']]
        except stripe.error.StripeError as e:
            print(':(')
        
        current_user.subscription_id = subscription_id
        current_user.membership_level = membership_level
        current_user.blogs_remaining_this_month = current_user.blogs_remaining_this_month + info.blogs_with_membership[membership_level]
        current_user.has_paid = True
        db.session.commit()

        member_to_delete = Member.query.filter_by(stripe_id=stripe_id).first()
        db.session.delete(member_to_delete)
        db.session.commit()

"""
Checks if the user has an already generated blog.

Returns:
    boolean: True if the user has a blog, False otherwise.
"""
def check_if_user_has_blog(current_user):
    blog = Blog.query.filter_by(user_id=current_user.id).first()
    if blog:
        return True
    return False



