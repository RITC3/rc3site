'''
emails.py - setup for email sending
'''
from flask import render_template
from flask.ext.mail import Message
from config import BASE_ADMINS
from decorators import async
from models import User
from app import app, mail
from time import sleep

@async
def send_async_email(msg):
    '''send an email in another thread, see decorators.py
    arg:
        msg - the Message object to send
    '''
    with app.app_context():
        mail.connect()
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    '''setup the email to be sent
    args:
        subject - the subject of the email to be sent
        recipients - the recipients of the email to be sent
        text_body - the body of the email to be sent, in plain text
        html_body - the body of the email to be sent, in html
    '''
    sender = ('RC3 E-Board', 'rc3club@gmail.com')
    msg = Message(subject, sender = sender, bcc = recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)

def send_welcome(user):
    '''send email upon registration
    arg:
        user - the user to send the welcome email to
    '''
    send_email("Welcome to RC3 {}!".format(user.nickname),
        [user.email],
        render_template("welcome_email.txt",
            user = user),
        render_template("welcome_email.html",
            user = user))

def send_newsletter(subject, body):
    '''send out the newsletter
    args:
        subject - the subject of the newsletter to send
        body - the name of the newsletter to send
    '''
    users = [ x.email for x in User.query.filter_by(newsletter = 1).all() ]
    #rit doesn't just let you bcc everyone, chunks of 20 work
    chunksize = 10
    for chunk in [users[x:x+chunksize] for x in range(0, len(users), chunksize)]:
        send_email(subject, chunk, body, body)
        sleep(0.05)

def contact_us(msg):
    '''send an email to the site admins
    arg:
        msg - the message to send
    '''
    send_email(msg[0], BASE_ADMINS, msg[1], msg[1])
