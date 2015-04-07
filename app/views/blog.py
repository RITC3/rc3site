from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from app import app, db

blog = Blueprint('blog', __name__, subdomain='blog')

@blog.route('/')
@blog.route('/index')
def blog_index():
    return render_template('blog/index.html')
