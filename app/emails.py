from flask import render_template
from flask.ext.mail import Message
from flask import current_app
from config import BASE_ADMINS
from decorators import async
from models import User
from app import app, mail
from time import sleep

@async
def send_async_email(msg):
    with app.app_context():
        mail.connect()
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    sender = ('RC3 E-Board', 'rc3club@gmail.com')
    msg = Message(subject, sender = sender, bcc = recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)

def send_welcome(user):
    send_email("Welcome to RC3 {}!".format(user.nickname),
        [user.email],
        render_template("welcome_email.txt",
            user = user),
        render_template("welcome_email.html",
            user = user))

def send_newsletter(subject,body):
    users = [ x.email for x in User.query.filter_by(newsletter = 1).all() ]
    for chunk in [users[x:x+20] for x in range(0, len(users), 20)]:
        send_email(subject, chunk, body, body)
        sleep(0.05)


def contact_us(msg):
    send_email(msg[0], BASE_ADMINS, msg[1], msg[1])
