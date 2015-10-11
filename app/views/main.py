"""
main.py - The main view fuction for the website. This defines each "route" and
what should happen when a user visits the page.
"""
from datetime import datetime
from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import db, lm, google
from app.models import *
from app.emails import contact_us, send_newsletter
from config import USER_ROLES
from sqlalchemy import desc
from random import randint
from app.forms import *

#defines the main path for the application
main = Blueprint('main', __name__)

def is_admin():
    if g.user.role == USER_ROLES['admin']:
        return True
    return False

def sort_user_scores(l, semester):
    '''Sorts users by score for the scoreboard
    args:
        l - the input list of users to be sorted
        semester - the semester to get the score for
    Note: does not return, modifies the original list
    '''
    for i in xrange(1, len(l)):
        j = i-1
        key = l[i]
        while (l[j].get_score(semester=semester) < key.get_score(semester=semester)) \
                and (j >= 0):
            l[j+1] = l[j]
            j -= 1
        l[j+1] = key

#look in the wiki for documentation on these decorators
@main.before_request
def before_request():
    '''Runs before every request to get information to be used in the
    rendered pages
    Gets the user object, current semester object, and semester list
    Also updates the user's last seen time
    '''
    g.user = current_user
    g.csemester = Semester.query.filter_by(current=True).first()
    g.route = request.path
    g.semesters = Semester.query.order_by(desc('id')).all()
    if "semester" not in session.keys() or session['semester'] \
            not in [ i.lname for i in g.semesters ]:
        session['semester'] = g.csemester.lname
    g.semester = session['semester']
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@main.route('/')
@main.route('/index')
def index():
    '''The default page of the app
    Returns: The rendered homepage or th page in the 'next' get parameter
    '''
    if request.args.get('next'):
        return redirect(url_for(request.args.get('next')))
    usern = g.user
    browser = request.user_agent.browser
    if browser == "firefox":
        flash("Firefox often doesn't play nice with Google OAuth. \
              You may want to try chrome if it won't let you login")

    #only show the user if they are not an admin
    all_users = [ user for user in
                 User.query.filter(User.role != USER_ROLES['admin']).all()
                 if user.get_score(semester=g.csemester) ]
    sort_user_scores(all_users, semester=g.csemester)

    return render_template("index.html",
                           title='Home',
                           user=usern,
                           topusers=all_users[:5],
                           semester=g.csemester)

@lm.user_loader
def load_user(id):
    '''Gets the current user object from the user id
    arg:
        id - the current user's id from the database
    Returns: the user object
    '''
    return User.query.get(int(id))

@main.route('/logout')
@login_required
def logout():
    '''The user logout page
    Returns: A redirect for the index page, after clearing the session
    '''
    logout_user()
    session.clear()
    return redirect(url_for('.index'))

@main.route('/login/authorized')
@google.authorized_handler
def authorized(response):
    '''Handles the OAuth response from Google
    Returns: a redirect to the index page, after logging the user in (or erroring)
    '''
    if response is None:
        flash('Login failed :(')
        return redirect(url_for('main.index'))

    session['google_token'] = (response['access_token'], '')
    me = google.get('userinfo')

    #is the user either from RIT or explicitly allowed?
    alloweduser = AllowedUser.query.filter_by(email=me.data['email'], ban=False).first()
    if me.data['hd'] != "g.rit.edu" and alloweduser is None:
        me = None
        response = None
        logout_user()
        session.clear()
        flash('You must log in with your RIT Email \
              or obtain special permission to log in from an administrator')
        return redirect(url_for('main.index'))

    #get the existing user, or create a new one
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
            username = username[:7] + str(randint(100, 999))
        user = User(nickname=nickname,
                    username=username,
                    email=me.data['email'],
                    role=USER_ROLES['user'])
        db.session.add(user)
        db.session.commit()
    if me.data['name'] and user.nickname is not me.data['name']:
        user.nickname = me.data['name']
        db.session.add(user)
        db.session.commit()
    elif me.data['given_name'] and user.nickname is not me.data['name']:
        user.nickname = me.data['given_name']
        db.session.add(user)
        db.session.commit()
    login_user(user, remember = False)
    return redirect(request.args.get('next') or url_for('main.index'))

@main.route('/user/<username>')
@login_required
def user(username):
    '''Profile page for a user
    arg:
        username - the name of the user
    Returns: the rendered profile page for the user
    '''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User not found.')
        abort(404)
    return render_template('user.html', title=user.nickname, user=user)

@main.route('/resources')
@login_required
def resources():
    '''The presentations section of the site
    Returns: the rendered resources page for the selected semester
    '''
    sem = Semester.query.filter_by(lname=session['semester']).first()
    if sem is None:
        return render_template('404.html', title='404'), 404
    pres = [ p for p in Presentation.query.order_by('week') if p.semester.lname == sem.lname ]
    return render_template('resources.html',
                           title='Resources',
                           pres_list=pres,
                           semester=sem)

@main.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    '''Allows editing a user's profile
    Returns: The profile editing page or the user's profile page when the edit
             is committed
    '''
    form = EditForm()
    if form.validate_on_submit():
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
        form.about_me.data = g.user.about_me
        form.major.data = g.user.major
        if g.user.newsletter == 1:
            form.newsletter.data = True
        else:
            form.newsletter.data = False
    return render_template('edit.html', title='Edit', form=form, user=g.user)

@main.route('/email', methods=['POST'])
def email():
    '''Sends an email to the rc3 admins
    Returns: a redirect for the contact us page after the email has been sent
    Note: Not implemented yet... perhaps not needed at all
    '''
    # Check post values
    if False:
        flash('Sorry, please try to send your message again')
        return redirect(url_for('main.contact'))
    # Spawn new process to send email
    flash('Your message has been sent!')
    return redirect(url_for('main.contact'))

@main.route('/scoreboard')
def scoreboard():
    '''The semester scoreboard page
    Returns: the rendered scoreboard page for the selected semester
    '''
    sem = Semester.query.filter_by(lname=session['semester']).first()
    if sem is None:
        return render_template('404.html', title='404'), 404
    all_users = [ user for user in User.query.all()
                 if user.role != USER_ROLES['admin'] and user.get_score(semester=sem) ]
    sort_user_scores(all_users, semester=sem)
    return render_template('scoreboard.html',
                           title='Scoreboard',
                           users=all_users,
                           semester=sem)

@main.route('/halloffame')
def halloffame():
    '''The scoreboard page for top all time scores across semesters
    Returns: the rendered hall of fame page
    '''
    users = [ user for user in User.query.all() if user.get_score() ]
    users = sorted(users, reverse=True)
    return render_template('halloffame.html', users=users[:10])

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    '''The page for contacting the RC3 admins
    Returns: the rendered contact page
    '''
    form = ContactUs()
    if form.validate_on_submit():
        subject = "{0} has sent the RC3 Admins a Message".format(form.name.data)
        message = render_template('contact_us_message.html',
                                  recp=form.email.data,
                                  name=form.name.data,
                                  msg=form.body.data)
        email = [subject, message]
        contact_us(email)
        flash('Your message has been sent!')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', title='Contact', form=form)

@main.route('/about')
def about():
    '''The page describing the club and it's members
    Returns: the rendered about page
    '''
    return render_template('about.html', title='About')

def add_points(user_id, challenge_id, points):
    """ add_points - adds or updates points for a user
        args:
            user_id - the id of the user who's score needs to be updates
            challenge_id - the id of the challenge to associate the points with
            points - the number of points to add
    """
    existing_score = \
        Score.query.filter_by(user_id=user_id,
                                challenge_id=challenge_id).first()
    if existing_score:
        existing_score.points = points
        db.session.add(existing_score)
        db.session.commit()
        return False
    else:
        semester_id = Challenge.query.filter_by(
            id=challenge_id
            ).first().semester_id
        new_score = Score(user_id=user_id,
                            challenge_id=challenge_id,
                            points=points,
                            semester_id=semester_id)
        db.session.add(new_score)
        db.session.commit()
        return True

@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    '''The administrative panel for the site
    Returns: The rendered admin panel
    '''
    if not is_admin():
        return render_template('404.html', title='404'), 404
    sess_sem = Semester.query.filter_by(lname=session['semester']).first()

    #challenge creation panel
    create_challenge = Create_Challenge()
    if request.form.get('submit', None) == 'Create Challenge':
        if create_challenge.validate_on_submit():
            challenge = Challenge(name = create_challenge.name.data,
                                  date = create_challenge.date.data,
                                  about = create_challenge.about.data,
                                  semester_id=sess_sem.id)
            db.session.add(challenge)
            db.session.commit()
            flash('Challenge created!')
            return redirect(url_for('main.admin'))

    challenges = [(c.id, c.name) for c in Challenge.query.filter_by(semester_id=sess_sem.id).all()]
    #mass score creating panel
    mass_score = Mass_Update_Score()
    mass_score.challenge.choices = challenges
    if request.form.get('submit', None) == 'Mass Update Score':
        for line in mass_score.massbox.data.split('\n'):
            user, points = line.split(",")
            try:
                userobj = User.query.filter_by(email=user + "@g.rit.edu").one()
                if not add_points(userobj.id, mass_score.challenge.data, points):
                    flash('Score updated for ' + user)
            except:
                flash('User ' + user + " doesn't exist or doesn't have an RIT email address")



    #single score creating panel
    update_score = Update_Score()
    update_score.challenge.choices = challenges
    if request.form.get('submit', None) == 'Update Score':
        if update_score.validate_on_submit():
            if add_points(update_score.user.data,
                          update_score.challenge.data,
                          update_score.points.data):
                flash('Score created!')
            else:
                flash('Score updated!')
            return redirect(url_for('main.admin'))

    #newsletter composing and sending panel
    newsletter_form = Send_Newsletter()
    if request.form.get('submit', None) == 'Send Newsletter':
        if newsletter_form.validate_on_submit():
            for media in newsletter_form['media']:
                if media.checked:
                    if str(media.data) == "mail":
                        send_newsletter(newsletter_form['subject'].data,
                                        newsletter_form['body'].data)
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

    #adding subscribers panel
    add_sub = Add_Subscriber()
    if request.form.get('submit', None) == 'Add Subscriber':
        if add_sub.validate_on_submit():
            users = add_sub.users.data.split()
            for user in users:
                email, major = user.split('/', 1)
                flash(email + ' is a ' + major)
            return redirect(url_for('main.admin'))

    #presentation adding/editing/deleting panel
    add_pres = Add_Presentation()
    if request.form.get('submit', None) == 'Add Presentation':
        if add_pres.validate_on_submit():
            new_pres = Presentation(name=add_pres.name.data,
                                    week=add_pres.week.data,
                                    link=add_pres.link.data,
                                    semester_id=sess_sem.id)
            db.session.add(new_pres)
            db.session.commit()
            flash(str("Presentation Week {} - {} Added".format(add_pres.week.data,
                                                               add_pres.name.data)))
            return redirect(url_for('main.admin'))
        else:
            flash("Invalid Presentation")
    edit_pres = EditPresentation()
    edit_pres.pres.choices = [ (x.id, "Week {} - {}".format(x.week, x.name))
                              for x in Presentation.query.filter_by(semester_id=sess_sem.id) ]
    if request.form.get('submit', None) == 'Edit Presentation':
        if edit_pres.validate_on_submit():
            pres = Presentation.query.filter_by(id=edit_pres.pres.data).first()
            if str(edit_pres.link.data) != "":
                pres.link = edit_pres.link.data
            if str(edit_pres.name.data) != "":
                pres.name = edit_pres.name.data
            db.session.add(pres)
            db.session.commit()
            flash("Presentation Week {} - {} editied successfully".format(pres.week,
                                                                          edit_pres.name.data))
            return redirect(url_for('main.admin'))
        else:
            flash("Invalid Presentation Edit")
    del_pres = DeletePresentation()
    del_pres.pres.choices = [ (x.id, "Week {} - {}".format(x.week, x.name))
                             for x in Presentation.query.filter_by(semester_id=sess_sem.id) ]
    if request.form.get('submit', None) == 'Delete Presentation':
        if edit_pres.validate_on_submit():
            pres = Presentation.query.filter_by(id=del_pres.data['pres']).first()
            name = "Week {} - {}".format(pres.week, pres.name)
            db.session.delete(pres)
            db.session.commit()
            flash("{} deleted".format(name))
            return redirect(url_for('main.admin'))

    #allowed user panel
    add_allowed_user = AddAllowedUser()
    if request.form.get('submit', None) == 'Add Allowed User':
        if add_allowed_user.validate_on_submit():
            allowed = AllowedUser(email=add_allowed_user.email.data,
                                  ban=add_allowed_user.ban.data)
            db.session.add(allowed)
            db.session.commit()
            flash('User "{}" added'.format(add_allowed_user.email.data))
            return redirect(url_for('main.admin'))
        else:
            flash('User not added')

    #use a dict for easier access of forms from the page
    ADMIN_FORMS = {'send_newsletter': newsletter_form,
                   'create_challenge': create_challenge,
                   'update_score': update_score,
                   'permission_user': permissions,
                   'add_subscriber': add_sub,
                   'add_presentation': add_pres,
                   'edit_presentation': edit_pres,
                   'delete_presentation': del_pres,
                   'add_allowed_user': add_allowed_user,
                   'mass_score': mass_score}
    return render_template('admin.html', title='Admin', ADMIN_FORMS=ADMIN_FORMS)

@main.route('/mailinglist')
def mailinglist():
    '''The mailing list page for admins to see who is signed up
    Returns: The rendered mailing list page
    '''
    if not is_admin():
        return render_template("404.html", title="Nope"), 404
    else:
        mlist = User.query.filter_by(newsletter=1)
        return render_template("mailinglist.html", mlist=mlist)

@main.route('/challenges')
def challenges():
    '''The challenge list page
    Returns: the rendered challenge list page for the selected semester
    '''
    try:
        sem = Semester.query.filter_by(lname=session['semester']).first()
        challenges = Challenge.query.filter_by(semester_id=sem.id)
    except:
            return render_template('404.html', title='404'), 404
    return render_template('challenges.html',
                           title='Challenges',
                           challenges=challenges,
                           user=g.user,
                           semester=sem)

@main.route('/challenges/<semester>/<chall>')
def challenge(semester, chall):
    '''The challenge viewing page
    args:
        semester - the semester the challenge is in
        chall - the challenge name
    Returns: The challenge viewing page
    '''
    sem = Semester.query.filter_by(lname=semester).first()
    if sem is None:
        return render_template('404.html', title='404'), 404
    challenge = Challenge.query.filter_by(name=chall, semester_id=sem.id).first()
    if challenge is None:
        return render_template('404.html', title='404'), 404
    return render_template('single_challenge.html',
                           title='Challenge',
                           challenge=challenge,
                           user=g.user,
                           semester=sem)

@main.route('/edit_challenge/<semester>/<chall>', methods = ['GET', 'POST'])
@login_required
def edit_challenge(semester, chall):
    '''The challenge editing page
    args:
        semester - the semester the challenge is in
        chall - the challenge name
    Returns: The challenge editing form, or the challenge page when the
             challenge is saved
    '''
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
        return redirect(url_for('main.challenge',
                                chall = form.name.data,
                                semester=sem.lname ))
    else:
        form.name.data = challenge.name
        form.about.data = challenge.about
        form.date.data = challenge.date
    return render_template('edit_challenge.html',
                           title='Edit Challenge',
                           form=form,
                           challenge=challenge)

@main.route('/unsubscribe')
@login_required
def unsubscribe():
    '''The newsletter unsubscription page
    Returns: a redirect for the index page after unsubscribing the user from
    the newsletter
    '''
    g.user.newsletter = 0
    db.session.add(g.user)
    db.session.commit()
    flash("You've been unsubscribed. To subscribe, go to your profile and choose Edit")
    return redirect(url_for('main.index'))

@main.route('/subscribe')
@login_required
def subscribe():
    '''The newsletter subscription page
    Returns: a redirect for the index page after subscribing the user to the newsletter
    '''
    g.user.newsletter = 1
    db.session.add(g.user)
    db.session.commit()
    flash("You've been subscribed. To unsubscribe, go to your profile and choose Edit")
    return redirect(url_for('main.index'))

@main.route('/signin')
def signin():
    '''The signin link that redirects to the google form for signing in to a meeting
    Returns: A redirect to the sign in form
    '''
    return redirect("http://goo.gl/forms/HsWUUBg4dW", code=302)

@main.route('/sem_switch/<semester>')
def sem_switch(semester):
    '''The page for switching semesters
    Returns: a redirect for the last page the user was on
    '''
    session['semester'] = semester
    return redirect(request.args.get('next'))
