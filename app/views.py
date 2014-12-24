#/usr/bin/python
"""
The main view fuction for the website. This defines each "route" and
what should happen when a user visits the page.
"""

import re
import sys
from datetime import datetime
from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, google
from models import User, USER_ROLES, Challenge, Score
from emails import send_welcome, contact_us, send_newsletter
from facebook import rc3_post
from config import USER_ROLES
import operator
#this is a fix for db_create, the forms class tries to access the DB before it is created if this isn't here
if not "db_create" in sys.argv[0]:
    from forms import LoginForm, EditForm, ContactUs, Create_Challenge, Update_Score, Send_Newsletter, Permission_User, Add_Subscriber, Edit_Challenge

def is_admin():
    if g.user.role == 1:
        return True
    else:
        return False


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@app.route('/')
@app.route('/index')
def index():
    user = g.user
    browser = request.user_agent.browser
    if browser == "firefox":
        flash("Firefox often doesn't play nice with Google OAuth. You may want to try chrome if it won't let you login")

    all_users = User.query.all()
    topusers = sorted(all_users, reverse=True)

    return render_template("index.html", title='Home', user=user, topusers=topusers[:5])

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login')
def login():
    session.pop('google_token', None)
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/ctf')
def ctf():
    return render_template("ctf.html", title='2014 CTF')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/login/authorized')
@google.authorized_handler
def authorized(response):
    if response is None:
        flash('Login failed :(')
        return redirect(url_for('index'))

    session['google_token'] = (response['access_token'], '')
    me = google.get('userinfo')

    if me.data['email'][-7:].lower() != "rit.edu":
        me = None
        response = None
        logout_user()
        session.clear()
        flash('You must log in with your RIT Email')
        return redirect(url_for('index'))

    user = User.query.filter_by(email=me.data['email']).first()
    if user is None:
        if me.data['name']:
            nickname = me.data['name']
        elif me.data['given_name']:
            nickname = me.data['given_name']
        else:
            #Use everything up to @ for username (RIT ID)
            nickname = me.data['email'].split('@')[0]
        username = me.data['email'].split('@')[0]
        user = User(nickname=nickname, username=username, email=me.data['email'], role=USER_ROLES['user'])
        db.session.add(user)
        db.session.commit()
    login_user(user, remember = False)
    return redirect(request.args.get('next') or url_for('index'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User not found.')
        abort(404)

    return render_template('user.html', title=user.nickname, user=user)

@app.route('/resources')
@login_required
def resources():
    res = []
    return render_template('resources.html', title='Resources')

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        g.user.major = form.major.data
        if form.newsletter.data:
            g.user.newsletter = 1
        else:
            g.user.newsletter = 0
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=g.user.username))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
        form.major.data = g.user.major
        if g.user.newsletter == 1:
            form.newsletter.data = True
        else:
            form.newsletter.data = False
    return render_template('edit.html', title='Edit', form=form, user=g.user)

@app.route('/email', methods=['POST'])
def email():
	# Check post values
    if False:
        flash('Sorry, please try to send your message again')
        return redirect(url_for('contact'))
    # Spawn new process to send email
    flash('Your message has been sent!')
    return redirect(url_for('contact'))

@app.route('/scoreboard')
def scoreboard():
    all_users = User.query.all()
    topusers = sorted(all_users, reverse=True)
    return render_template('scoreboard.html', title='Scoreboard', users=topusers)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactUs()
    if form.validate_on_submit():
        subject = "{0} has sent the RC3 Admins a Message".format(form.name.data)
        message = render_template('contact_us_message.html', recp=form.email.data, name=form.name.data, msg=form.body.data)
        email = [subject, message]
        contact_us(email)
        flash('Your message has been sent!')
        return redirect(url_for('contact'))
    return render_template('contact.html', title='Contact', form=form)

@app.route('/about')
def about():
    resources= []
    return render_template('about.html', title='About')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not is_admin():
        return render_template('404.html', title='404'), 404
    create_challenge = Create_Challenge()
    if request.form.get('submit', None) == 'Create Challenge':
        if create_challenge.validate_on_submit():
            challenge = Challenge(name = create_challenge.name.data, date = create_challenge.date.data, about = create_challenge.about.data)
            db.session.add(challenge)
            db.session.commit()
            flash('Challenge created!')
            return redirect(url_for('admin'))
    update_score = Update_Score()
    #update_score.choices = [(c.id, c.name) for c in Challenge.query.order_by('date')] query shit right at some point
    if request.form.get('submit', None) == 'Update Score':
        if update_score.validate_on_submit():
            existing_score = Score.query.filter_by(user_id=update_score.data['user'], challenge_id=update_score.data['challenge']).first()
            if existing_score:
                existing_score.points = update_score['points'].data
                db.session.add(existing_score)
                db.session.commit()
                flash('Score updated!')
                return redirect(url_for('admin'))
            else:
                new_score = Score(user_id=update_score.data['user'], challenge_id=update_score.data['challenge'], points=update_score.data['points'])
                db.session.add(new_score)
                db.session.commit()
                flash('Score created!')
                return redirect(url_for('admin'))
    newsletter_form = Send_Newsletter()
    if request.form.get('submit', None) == 'Send Newsletter':
        if newsletter_form.validate_on_submit():
            for media in newsletter_form['media']:
                if media.checked:
                    if media.data == "mail":
                        send_newsletter(newsletter_form['subject'].data, newsletter_form['body'].data)
                        #flash('Sent newsletter to {0}'.format(str(users)))
                    if media.data == "facebook":
                        result = rc3_post()
                        flash(str(result))
                    else:
                        flash("Sorry, {0} hasn't been implemented yet".format(media.data))
            return redirect(url_for('admin'))
    permissions = Permission_User()
    if request.form.get('submit', None) == 'Update User':
        if permissions.validate_on_submit():
            usr = permissions.user.data
            updated_user = User.query.filter_by(id=usr).first()
            updated_user.role = permissions.role.data
            updated_user.position = permissions.position.data
            db.session.add(updated_user)
            db.session.commit()
            if updated_user.role == 1:
                role = "an Admin."
            else:
                role = "a user."
            flash(str("{0} is now {1}".format(updated_user.nickname, role)))
            #Send email alerting this happened
            return redirect(url_for('admin'))
    add_sub = Add_Subscriber()
    if request.form.get('submit', None) == 'Add Subscriber':
        if add_sub.validate_on_submit():
            users = add_sub.users.data.split()
            for user in users:
                email, major = user.split('/', 1)
                flash(email + ' is a ' + major)
            return redirect(url_for('admin'))


    ADMIN_FORMS = {'send_newsletter':newsletter_form, 'create_challenge':create_challenge, 'update_score':update_score, 'permission_user':permissions, 'add_subscriber':add_sub}
    return render_template('admin.html', title='Admin', ADMIN_FORMS=ADMIN_FORMS)

@app.route('/mailinglist')
def mailinglist():
	#if not is_admin():
    #    return render_template("404.html", title="Nope"), 404
    #else:
    #mlist = User.query.filter_by(newsletter=1)
    #return mlist
    return render_template("404.html", title="Nope"), 404


@app.route('/challenges')
def challenges():
    challenges = Challenge.query.all()
    return render_template('challenges.html', title='Challenges', challenges=challenges, user=g.user)

@app.route('/challenge/<chall>')
def challenge(chall):
    challenge = Challenge.query.filter_by(name=chall).first()
    return render_template('single_challenge.html', title='Challenge', challenge=challenge, user=g.user)

@app.route('/edit_challenge/<chall>', methods = ['GET','POST'])
@login_required
def edit_challenge(chall):
    #if not is_admin():
    #    return render_template('404.html', title='404'), 404
    challenge = Challenge.query.filter_by(name=chall).first()
    form = Edit_Challenge(challenge.name)
    if form.validate_on_submit():
        challenge.name = form.name.data
        challenge.about = form.about.data
        challenge.date = form.date.data
        db.session.add(challenge)
        db.session.commit()
        flash('Your changes have been saved!')
        return redirect(url_for('challenge', chall = form.name.data ))
    else:
        form.name.data = challenge.name
        form.about.data = challenge.about
        form.date.data = challenge.date
    return render_template('edit_challenge.html', title='Edit Challenge', form=form, challenge=challenge)

@app.route('/unsubscribe')
@login_required
def unsubscribe():
    g.user.newsletter = 0
    db.session.add(g.user)
    db.session.commit()
    flash("You've been unsubscribed. To subscribe, go to your profile and choose Edit")
    return redirect(url_for('index'))

@app.route('/subscribe')
@login_required
def subscribe():
    g.user.newsletter = 1
    db.session.add(g.user)
    db.session.commit()
    flash("You've been subscribed. To unsubscribe, go to your profile and choose Edit")
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', title='404'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
