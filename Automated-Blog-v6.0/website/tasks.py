from celery import shared_task
import requests
from . import db
from .models import Blog
from .models import User
import BlogWriter
from time import sleep
import stripe
import os
from .info import prices, blogs_with_membership

@shared_task(bind=True)
def add_blog(self, title, additional_information, user_id):

    print('Starting task')
    title = title
    additional_information = additional_information
    user_id = user_id
    
    outline = BlogWriter.BlogWriter.writeBlogOutline(title)
    content = BlogWriter.BlogWriter.writeBlog(title=title, outline=outline, additional_information=additional_information)
    image_url = get_images(BlogWriter.BlogWriter.getSubject(title=title))

    if image_url != '':
        content = f'<img src="{get_images(BlogWriter.BlogWriter.getSubject(title=title))}" alt="blog image" width="100%" height="auto" /> \n' + content

    db.session.add(Blog(blog_title=title, blog_content=content, user_id=user_id, image_url=image_url))
    db.session.commit()

    return "Blog added successfully"

@shared_task(bind=True)
def check_members():
    users = User.query.all()
    for user in users:
        try:
            if user.membership_level != 'Free':
                stripe.api_key = os.environ.get('stripe_secret_key')

                subscription_id = user.subscription_id
                print(subscription_id)
                if subscription_id != None:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    status = subscription['status']
                else:
                    continue

                if status == 'active':
                    user.blogs_remaining_this_month = info.blogs_with_membership[user.membership_level] + user.blogs_remaining_this_month
                    db.session.commit()
        except stripe.error.StripeError as e:
            print("Error:", str(e))

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