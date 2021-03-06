'''
__init__.py - Initialize the application, logins, and its views
'''
import os
import facebook
from flask import Flask, render_template, request, session, url_for
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, logout_user, login_required
from flask_oauthlib.client import OAuth
from config import basedir, GOOGLE_CONSUMER_KEY, GOOGLE_CONSUMER_SECRET, \
BASE_ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, FACEBOOK_TOKEN
from flask.ext.admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import MenuLink
from flask_admin.contrib.fileadmin import FileAdmin

# Initialize the app and database, import the config
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

#setup Google oauth for login
oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key= GOOGLE_CONSUMER_KEY,
    consumer_secret= GOOGLE_CONSUMER_SECRET,
    request_token_params={
        'scope' : 'https://www.googleapis.com/auth/userinfo.email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url = None,
    access_token_method = 'POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url = 'https://accounts.google.com/o/oauth2/auth'
)

#create the login manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

#setup mail
mail = Mail(app)

#this starts the app
from app import models
db.create_all()
db.session.commit()
from app.views import irsec, main, blog

#error handlers, login, and google auth tokengetter are global
@app.errorhandler(404)
def not_found_error(error):
    '''The error handler for invalid pages
    Returns: the rendered 404 template
    '''
    return render_template('404.html')

@app.errorhandler(500)
def internal_error(error):
    '''The error handler for internal errors
    Returns: the rendered 500 template
    '''
    db.session.rollback()
    return render_template('500.html'), 500

@google.tokengetter
def get_google_oauth_token():
    '''Gets a google oauth token
    Returns: the token
    '''
    return session.get('google_token')

@app.route('/login')
def login():
    '''User login page
    Returns: a google authorization handler
    '''
    session.pop('google_token', None)
    return google.authorize(callback=url_for('main.authorized', _external=True))

#blog admin setup
admin = Admin(app, 'Blog Admin', subdomain="blog",
              template_mode='bootstrap3',
              index_view=blog.ProtectedIndexView())
admin.add_link(MenuLink(name='Back to Site', url='/'))
admin.add_view(blog.PostModelView())
admin.add_view(blog.ProtectedFileAdmin(os.path.join(basedir, 'app/static/bloguploads'), '/static/bloguploads/', name="Blog Uploads"))

#blueprints are each section of the app
#app.register_blueprint(blog.blog)
app.register_blueprint(irsec.irsec)
app.register_blueprint(main.main)


'''for rule in app.url_map.iter_rules():
        #import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
    print rule.endpoint
    '''
"""
if not app.debug:
    import logging

    ## Email Logging

    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@'
        + MAIL_SERVER, ADMINS, 'RC3 Site failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    ## File Logging

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/rc3.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:
        %(messages)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('RC3 startup')

"""
