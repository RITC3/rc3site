from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from app import app, db

irsec = Blueprint('irsec', __name__, subdomain='irsec', static_folder="../static")

@irsec.route('/')
@irsec.route('/index')
def index():
    return render_template('irsec/index.html', title="Home")

@irsec.route('/signup')
def signup():
    return render_template('irsec/signup.html', title="Signup")

@irsec.route('/about')
def about():
    return render_template('irsec/about.html', title="About")

@irsec.errorhandler(404)
def not_found_error(error):
    return render_template('irsec/404.html')
