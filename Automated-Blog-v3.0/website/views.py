from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
import json
import BlogWriter

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@views.route('/generate-blog', methods=['GET', 'POST'])
@login_required
def generateBlog():
    content = ''
    if request.method == 'POST':
        title = request.form.get('blog-title')
        topic = request.form.get('blog-topic')
        emulation_text = request.form.get('emulation-text')
        keywords = request.form.get('keywords')
        links = request.form.get('links')
        length = request.form.get('length')
        image = request.form.get('file')   

        content = BlogWriter.BlogWriter.writeBlog(title=title, topic=topic, emulation=emulation_text, keywords=keywords, links=links, length=length)             

    return render_template("generate_blog.html", user=current_user, text=content)
