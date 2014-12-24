from flask import render_template
from flask.ext.mail import Message
from app import mail
from config import BASE_ADMINS
from decorators import async
from models import User

@async
def send_async_email(msg):
    mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    sender = BASE_ADMINS[0]
    msg = Message(subject, sender = sender, recipients = recipients)
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
    users = User.query.filter_by(newsletter = 1)
    with mail.connect() as conn:
        for user in users:
            send_email(subject, [user.email], body, body)


def contact_us(msg):
    send_email(msg[0], BASE_ADMINS, msg[1], msg[1])
