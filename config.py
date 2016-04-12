import os

#get the path that the app is running in
basedir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(basedir, 'base_newsletter.html') , 'r') as f:
    BASE_NEWSLETTER = f.read()

#get private application resources
f = open(os.path.join(basedir, 'app.stuff') , 'r')

CSRF_ENABLED = True
SERVER_NAME = 'rc3.club'

#setup database
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') + '?check_same_thread=False'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

#get constants from file
SECRET_KEY = f.readline().strip()
GOOGLE_CONSUMER_KEY = f.readline().strip()
GOOGLE_CONSUMER_SECRET = f.readline().strip()
MAIL_SERVER = f.readline().strip()
MAIL_PORT = f.readline().strip()
MAIL_USE_SSL = f.readline().strip()
MAIL_USERNAME = f.readline().strip()
MAIL_PASSWORD = f.readline().strip()
FACEBOOK_TOKEN = f.readline().strip()
BASE_ADMINS = [ x.rstrip() for x in f.readline().split(',') ]
f.close()
SOCIAL_MEDIA=['mail','facebook','twitter','reddit']
DEFAULT_MEDIA=['mail']
USER_ROLES = {'admin':1,'user':0}
