from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from app import app, db

irsec = Blueprint('irsec', __name__, subdomain='irsec')

@irsec.route('/')
@irsec.route('/index')
def irsec_index():
    return render_template('irsec/index.html')
