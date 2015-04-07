#!/usr/bin/python
"""
The main view fuction for the website. This defines each "route" and
what should happen when a user visits the page.
"""

import re
import sys
from datetime import datetime
from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, google
from app.models import *
from app.emails import send_welcome, contact_us, send_newsletter
from app.facebook import rc3_post
from config import USER_ROLES
from sqlalchemy import desc
import operator
from random import randint
#this is a fix for db_create, the forms class tries to access the DB before it is created if this isn't here
if not "db_create" in sys.argv[0]:
    from app.forms import *

main = Blueprint('main', __name__)

def is_admin():
    if g.user.role == 1:
        return True
    else:
        return False

def sort_user_scores(l, semester):
    for i in xrange(1, len(l)):
        j = i-1
        key = l[i]
        while (l[j].get_score(semester=semester) < key.get_score(semester=semester)) and (j >= 0):
           l[j+1] = l[j]
           j -= 1
        l[j+1] = key

@main.before_request
def before_request():
    g.user = current_user
    g.csemester = Semester.query.filter_by(current=True).first()
    g.route = request.path
    g.semesters = Semester.query.order_by(desc('id'))
    if "semester" not in session.keys() or session['semester'] not in [ i.lname for i in g.semesters ]:
        session['semester'] = g.csemester.lname
    g.semester = session['semester']
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@main.route('/')
@main.route('/index')
def index():
    if request.args.get('next'):
        return redirect(url_for(request.args.get('next')))
    usern = g.user
    browser = request.user_agent.browser
    if browser == "firefox":
        flash("Firefox often doesn't play nice with Google OAuth. You may want to try chrome if it won't let you login")

    #only show the user if they are an admin
    all_users = [ user for user in User.query.filter(User.role != USER_ROLES['admin']).all() if user.get_score(semester=g.csemester) ]
    sort_user_scores(all_users, semester=g.csemester)

    return render_template("index.html", title='Home', user=usern, topusers=all_users[:5], semester=g.csemester)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@main.route('/login')
def login():
    session.pop('google_token', None)
    return google.authorize(callback=url_for('main.authorized', _external=True))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('main.index'))

@main.route('/login/authorized')
@google.authorized_handler
def authorized(response):
    if response is None:
        flash('Login failed :(')
        return redirect(url_for('main.index'))

    session['google_token'] = (response['access_token'], '')
    me = google.get('userinfo')

    alloweduser = AllowedUser.query.filter_by(email=me.data['email'], ban=False).first()
    if me.data['email'][-7:].lower() != "rit.edu" and alloweduser is None:
        me = None
        response = None
        logout_user()
        session.clear()
        flash('You must log in with your RIT Email or obtain special permission to log in from an administrator')
        return redirect(url_for('main.index'))

    user = User.query.filter_by(email=me.data['email']).first()
    if user is None:
        if me.data['name']:
            nickname = me.data['name']
        elif me.data['given_name']:
            nickname = me.data['given_name']
        else:
            #Use everything up to @ for username (RIT ID)
            nickname = me.data['email'].split('@')[0][:10]
        #if the email address > 10 digits truncate
        username = me.data['email'].split('@')[0][:10]
        #if the username already exists mainend a random integer to the end
        while User.query.filter_by(username=username).first() is not None:
            username = username[:7] + str(randint(100,999))
        user = User(nickname=nickname, username=username, email=me.data['email'], role=USER_ROLES['user'])
        db.session.add(user)
        db.session.commit()
    login_user(user, remember = False)
    return redirect(request.args.get('next') or url_for('main.index'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User not found.')
        abort(404)

    return render_template('user.html', title=user.nickname, user=user)

@main.route('/resources')
@login_required
def resources():
    sem = Semester.query.filter_by(lname=session['semester']).first()
    if sem == None:
        return render_template('404.html', title='404'), 404
    pres = [ p for p in Presentation.query.order_by('week') if p.semester.lname == sem.lname ]
    return render_template('resources.html', title='Resources', pres_list=pres, semester=sem)

#News section
@main.route('/news')
@login_required
def news():
    return redirect(url_for('main.news_hist', num=1))

#Articles on Articles (extra pages for 25+ articles)
@main.route('/news/<num>')
@login_required
def news_hist(num):
    num = int(num)-1
    arts_per_page = 25
    more = True
    art = News.query.order_by(desc('id'))
    if len(art[(num*arts_per_page):]) <= arts_per_page:
        more = False
    art = art[(num*arts_per_page):arts_per_page*(num+1)]
    if not art or art is None:
        return render_template('404.html', title='404'), 404
    else:
        return render_template('news.html', title='News', articles=art, num=num+1, more=more)

@main.route('/edit', methods = ['GET', 'POST'])
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
        return redirect(url_for('main.user', username=g.user.username))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
        form.major.data = g.user.major
        if g.user.newsletter == 1:
            form.newsletter.data = True
        else:
            form.newsletter.data = False
    return render_template('edit.html', title='Edit', form=form, user=g.user)

@main.route('/email', methods=['POST'])
def email():
    # Check post values
    if False:
        flash('Sorry, please try to send your message again')
        return redirect(url_for('main.contact'))
    # Spawn new process to send email
    flash('Your message has been sent!')
    return redirect(url_for('main.contact'))

@main.route('/scoreboard')
def scoreboard():
    sem = Semester.query.filter_by(lname=session['semester']).first()
    if sem == None:
        return render_template('404.html', title='404'), 404
    all_users = [ user for user in User.query.all() if user.role != USER_ROLES['admin'] and user.get_score(semester=sem) ]
    sort_user_scores(all_users, semester=sem)
    return render_template('scoreboard.html', title='Scoreboard', users=all_users, semester=sem)

@main.route('/halloffame')
def halloffame():
    users = [ user for user in User.query.all() if user.get_score() ]
    users = sorted(users, reverse=True)
    return render_template('halloffame.html', users=users[:10])

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactUs()
    if form.validate_on_submit():
        subject = "{0} has sent the RC3 Admins a Message".format(form.name.data)
        message = render_template('contact_us_message.html', recp=form.email.data, name=form.name.data, msg=form.body.data)
        email = [subject, message]
        contact_us(email)
        flash('Your message has been sent!')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', title='Contact', form=form)

@main.route('/about')
def about():
    return render_template('about.html', title='About')


@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not is_admin():
        return render_template('404.html', title='404'), 404

    sess_sem = Semester.query.filter_by(lname=session['semester']).first()
    create_challenge = Create_Challenge()
    if request.form.get('submit', None) == 'Create Challenge':
        if create_challenge.validate_on_submit():
            challenge = Challenge(name = create_challenge.name.data, date = create_challenge.date.data, about = create_challenge.about.data, semester_id=sess_sem.id)
            db.session.add(challenge)
            db.session.commit()
            flash('Challenge created!')
            return redirect(url_for('main.admin'))

    update_score = Update_Score()
    update_score.challenge.choices = [(c.id, c.name) for c in Challenge.query.filter_by(semester_id=sess_sem.id).all()]
    if request.form.get('submit', None) == 'Update Score':
        if update_score.validate_on_submit():
            existing_score = Score.query.filter_by(user_id=update_score.data['user'], challenge_id=update_score.data['challenge']).first()
            if existing_score:
                existing_score.points = update_score['points'].data
                db.session.add(existing_score)
                db.session.commit()
                flash('Score updated!')
                return redirect(url_for('main.admin'))
            else:
                semester_id = Challenge.query.filter_by(id=update_score.data['challenge']).first().semester_id
                new_score = Score(user_id=update_score.data['user'], challenge_id=update_score.data['challenge'], points=update_score.data['points'], semester_id=semester_id)
                db.session.add(new_score)
                db.session.commit()
                flash('Score created!')
                return redirect(url_for('main.admin'))

    newsletter_form = Send_Newsletter()
    if request.form.get('submit', None) == 'Send Newsletter':
        if newsletter_form.validate_on_submit():
            for media in newsletter_form['media']:
                if media.checked:
                    if str(media.data) == "mail":
                        send_newsletter(newsletter_form['subject'].data, newsletter_form['body'].data)
                        flash('Sent newsletter')
                    else:
                        flash("Sorry, {0} hasn't been implemented yet".format(media.data))
            return redirect(url_for('main.admin'))

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
            return redirect(url_for('main.admin'))

    add_sub = Add_Subscriber()
    if request.form.get('submit', None) == 'Add Subscriber':
        if add_sub.validate_on_submit():
            users = add_sub.users.data.split()
            for user in users:
                email, major = user.split('/', 1)
                flash(email + ' is a ' + major)
            return redirect(url_for('main.admin'))

    #presentation form generation
    add_pres = Add_Presentation()
    if request.form.get('submit', None) == 'Add Presentation':
        if add_pres.validate_on_submit():
            new_pres = Presentation(name=add_pres.name.data, week=add_pres.week.data, link=add_pres.link.data, semester_id=sem_sess.id)
            db.session.add(new_pres)
            db.session.commit()
            flash(str("Presentation Week {} - {} Added".format(add_pres.week.data, add_pres.name.data)))
            return redirect(url_for('main.admin'))
        else:
            flash("Invalid Presentation")

    #presentation editing
    edit_pres = EditPresentation()
    edit_pres.pres.choices = [ (x.id, "Week {} - {}".format(x.week, x.name)) for x in Presentation.query.filter_by(semester_id=sess_sem.id) ]
    if request.form.get('submit', None) == 'Edit Presentation':
        if edit_pres.validate_on_submit():
            pres = Presentation.query.filter_by(id=edit_pres.pres.data).first()
            if str(edit_pres.link.data) != "":
                pres.link = edit_pres.link.data
            if str(edit_pres.name.data) != "":
                pres.name = edit_pres.name.data
            db.session.add(pres)
            db.session.commit()
            flash("Presentation Week {} - {} editied successfully".format(pres.week, edit_pres.name.data))
            return redirect(url_for('main.admin'))
        else:
            flash("Invalid Presentation Edit")

    #presentation deleting
    del_pres = DeletePresentation()
    del_pres.pres.choices = [ (x.id, "Week {} - {}".format(x.week, x.name)) for x in Presentation.query.filter_by(semester_id=sess_sem.id) ]
    if request.form.get('submit', None) == 'Delete Presentation':
        if edit_pres.validate_on_submit():
            pres = Presentation.query.filter_by(id=del_pres.data['pres']).first()
            name = "Week {} - {}".format(pres.week, pres.name)
            db.session.delete(pres)
            db.session.commit()
            flash("{} deleted".format(name))
            return redirect(url_for('main.admin'))

    #Uploading news article
    upload_article = AddNewsArticle()
    if request.form.get('submit', None) == 'Upload Article':
        if upload_article.validate_on_submit():
            article = News(title = upload_article.title.data, description = upload_article.description.data, link = upload_article.link.data, date = upload_article.date.data, semester_id=g.csemester.id)
            db.session.add(article)
            db.session.commit()
            flash('Article Uploaded')
            return redirect(url_for('main.admin'))
        else:
            flash('Article not Uploaded')

    add_allowed_user = AddAllowedUser()
    if request.form.get('submit', None) == 'Add Allowed User':
        if add_allowed_user.validate_on_submit():
            allowed = AllowedUser(email=add_allowed_user.email.data, ban=add_allowed_user.ban.data)
            db.session.add(allowed)
            db.session.commit()
            flash('User "{}" added'.format(add_allowed_user.email.data))
            return redirect(url_for('main.admin'))
        else:
            flash('User not added')

    ADMIN_FORMS = {'send_newsletter':newsletter_form, 'create_challenge':create_challenge, 'update_score':update_score, 'permission_user':permissions, 'add_subscriber':add_sub, 'add_presentation':add_pres, 'edit_presentation':edit_pres, 'delete_presentation':del_pres, 'upload_article':upload_article, 'add_allowed_user':add_allowed_user}
    return render_template('admin.html', title='Admin', ADMIN_FORMS=ADMIN_FORMS)

@main.route('/mailinglist')
def mailinglist():
    if not is_admin():
        return render_template("404.html", title="Nope"), 404
    else:
        mlist = User.query.filter_by(newsletter=1)
        return render_template("mailinglist.html", mlist=mlist)

@main.route('/challenges')
def challenges():
    try:
        sem = Semester.query.filter_by(lname=session['semester']).first()
        challenges = Challenge.query.filter_by(semester_id=sem.id)
    except:
            return render_template('404.html', title='404'), 404
    return render_template('challenges.html', title='Challenges', challenges=challenges, user=g.user, semester=sem)

@main.route('/challenges/<semester>/<chall>')
def challenge(semester, chall):
    sem = Semester.query.filter_by(lname=semester).first()
    if sem == None:
        return render_template('404.html', title='404'), 404
    challenge = Challenge.query.filter_by(name=chall, semester_id=sem.id).first()
    if challenge == None:
        return render_template('404.html', title='404'), 404
    return render_template('single_challenge.html', title='Challenge', challenge=challenge, user=g.user, semester=sem)

@main.route('/edit_challenge/<semester>/<chall>', methods = ['GET','POST'])
@login_required
def edit_challenge(semester, chall):
    if not is_admin():
        return render_template('404.html', title='404'), 404
    sem = Semester.query.filter_by(lname=semester).first()
    challenge = Challenge.query.filter_by(name=chall, semester_id=sem.id).first()
    form = Edit_Challenge(challenge.name)
    if form.validate_on_submit():
        challenge.name = form.name.data
        challenge.about = form.about.data
        challenge.date = form.date.data
        db.session.add(challenge)
        db.session.commit()
        flash('Your changes have been saved!')
        return redirect(url_for('main.challenge', chall = form.name.data, semester=sem.lname ))
    else:
        form.name.data = challenge.name
        form.about.data = challenge.about
        form.date.data = challenge.date
    return render_template('edit_challenge.html', title='Edit Challenge', form=form, challenge=challenge)

@main.route('/unsubscribe')
@login_required
def unsubscribe():
    g.user.newsletter = 0
    db.session.add(g.user)
    db.session.commit()
    flash("You've been unsubscribed. To subscribe, go to your profile and choose Edit")
    return redirect(url_for('main.index'))

@main.route('/subscribe')
@login_required
def subscribe():
    g.user.newsletter = 1
    db.session.add(g.user)
    db.session.commit()
    flash("You've been subscribed. To unsubscribe, go to your profile and choose Edit")
    return redirect(url_for('main.index'))

@main.route('/signin')
def signin():
    return redirect("http://goo.gl/forms/HsWUUBg4dW", code=302)

@main.route('/sem_switch/<semester>')
def sem_switch(semester):
    session['semester'] = semester
    return redirect(request.args.get('next'))

@main.errorhandler(404)
def not_found_error(error):
    return render_template('404.html')

