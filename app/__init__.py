import os
import facebook
from flask import Flask
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_oauthlib.client import OAuth
from config import basedir, GOOGLE_CONSUMER_KEY, GOOGLE_CONSUMER_SECRET, BASE_ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, FACEBOOK_TOKEN

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)


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



lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

mail = Mail(app)

from app import views, models
"""
if not app.debug:
	import logging

	## Email Logging

	from logging.handlers import SMTPHandler
	credentials = None
	if MAIL_USERNAME or MAIL_PASSWORD:
		credentials = (MAIL_USERNAME, MAIL_PASSWORD)
	mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'RC3 Site failure', credentials)
	mail_handler.setLevel(logging.ERROR)
	app.logger.addHandler(mail_handler)

	## File Logging

	from logging.handlers import RotatingFileHandler
	file_handler = RotatingFileHandler('tmp/rc3.log', 'a', 1 * 1024 * 1024, 10)
	file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(messages)s [in %(pathname)s:%(lineno)d]'))
	app.logger.setLevel(logging.INFO)
	file_handler.setLevel(logging.INFO)
	app.logger.addHandler(file_handler)
	app.logger.info('RC3 startup')

	"""