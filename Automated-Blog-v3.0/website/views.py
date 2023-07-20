from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Blog
from . import db
import json
import BlogWriter
import stripe
import config

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
    return render_template("dashboard.html", user=current_user)

@views.route('/generate-blog', methods=['GET', 'POST'])
@login_required
def generateBlog():
    content = ''
    title = ''

    if request.method == 'POST':
        title = request.form.get('blog-title')
        topic = request.form.get('blog-topic')
        emulation_text = request.form.get('emulation-text')
        keywords = request.form.get('keywords')
        links = request.form.get('links')
        length = request.form.get('length')
        publish_date = request.form.get('publish-date')
        image = request.form.get('file')   

        content = BlogWriter.BlogWriter.writeBlog(title=title, topic=topic, emulation=emulation_text, keywords=keywords, links=links, length=length, )             

        new_blog = Blog(blog_title=title, blog_content=content, publish_date=publish_date, user_id=current_user.id)
        db.session.add(new_blog)
        db.session.commit()

        current_user.free_blogs_remaining = 0
        db.session.commit()


    return render_template("generate_blog.html", user=current_user, title=title, content=content)
