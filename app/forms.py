'''
forms.py - Defines all of the html forms for the app
'''
import re
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, IntegerField, \
    SubmitField, widgets, SelectMultipleField, RadioField
from wtforms.fields import DateField, TextAreaField
from wtforms.validators import Length, DataRequired
from datetime import datetime
from app.models import *
from config import SOCIAL_MEDIA, DEFAULT_MEDIA, USER_ROLES, BASE_NEWSLETTER

def get_sorted_userlist():
    '''Sorts a the userlist by nickname
    Returns: a list of all users sorted alphabetically by nickname
    '''
    userchoices = []
    users = User.query.all()
    users.sort(key=lambda user: user.nickname.lower())
    for user in users:
        if user.nickname == user.username:
            userchoices.append((user.id, "{0}".format(user.username)))
        else:
            userchoices.append((user.id, "{0} - {1}".format(user.nickname, user.username)))
    return userchoices


'''''''''''''''''''''''
Main site forms
'''''''''''''''''''''''
class MultiCheckboxField(SelectMultipleField):
    '''multi select checkboxes from ListWidget, SelectMultiple, and CheckboxInput
    Parent: wtforms.SelectMultipleField
    '''
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

    def __call__(self, field, **kwargs):
        '''when
        args:
            field - the checkbox field to be set
        kwargs:
            checked - the checked attribute of the box
        Returns: the result of the parent __call__ function
        '''
        if getattr(field, 'checked', field.data):
            kwargs['checked'] = True
            return super(CheckboxInput, self).__call__(field, **kwargs)


class EditForm(Form):
    '''For editing of a users profile
    Parent: flask.ext.wtf.Form
    Attributes:
        nickname - the nickname form field, required
        about_me - the about me form field, min = 0, max = 300
        major - the major form field, min = 0, max = 64
        newsletter - newsletter signup field
    '''
    nickname = TextField('nickname', validators = [DataRequired()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 300)])
    major = TextField('major', validators = [Length(min = 0, max = 64)])
    newsletter = BooleanField('newsletter', widget= widgets.CheckboxInput())

    def __init__(self, original_nickname, *args, **kwargs):
        '''initializes the class, calls parent class __init__ and sets original
        nickname
        args:
            original_nickname - the nickname before the update
        '''
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        '''validate the form input
        Extra conditions:
            nickname name must be unique
            nickname name must be changed
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname = self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


class Edit_Challenge(Form):
    '''Form for editing a challenge
    Parent: flask.ext.wtf.Form
    Attributes:
        name - the name of the challenge, required, min = 1, max = 64
        date - the date of the challenge, required
        about - description of the challenge, min = 0, max = 1000
        submit - the submit field button
    '''
    name = TextField('name', validators = [DataRequired(), Length(min = 1, max = 64)])
    date = DateField('date', validators = [DataRequired()])
    about = TextAreaField('about', validators = [Length(min = 0, max = 1000)])
    submit = SubmitField('submit')

    def __init__(self, original_name, *args, **kwargs):
        '''initializes the class, calls parent class __init__ and sets original
        name
        args:
            original_name - the nickname before the update
        '''
        Form.__init__(self, *args, **kwargs)
        self.original_name = original_name

    def validate(self):
        '''validate the form input
        Extra conditions:
            challenge name must be unique
            challenge name must be changed
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        name = Challenge.query.filter_by(name = self.name.data).first()
        if self.name.data == self.original_name:
            return True
        if name is not None:
            self.name.errors.append('A challenge with this name already exists. Please use a new one.')
            return False
        return True


class ContactUs(Form):
    '''Form for contacting the RC3 admins
    Parent: flask.ext.wtf.Form
    Attributes:
        name - name of the sender, required
        email - the email address of the sender, min = 6, max = 140
        about - the body of the email, min = 1, max = 1000
    '''
    name = TextField('name', validators = [DataRequired()])
    email = TextField('email', validators = [Length(min = 6, max = 140)])
    body = TextAreaField('body', validators = [Length(min = 1, max = 1000)])

    def validate(self):
        '''validate the form input
        Returns: True on sucessful validation, False when validation fails
        '''
        return Form.validate(self)


class Create_Challenge(Form):
    '''Form for creating a challenge
    Parent: flask.ext.wtf.Form
    Attributes:
        name - the name of the challenge, required, min = 1, max = 64
        date - the date of the challenge, required
        about - description of the challenge, min = 0, max = 1000
        submit - the submit field button
    '''
    name = TextField('name', validators = [DataRequired(), Length(min = 1, max = 64)])
    date = DateField('date', validators = [DataRequired()], default = datetime.now())
    about = TextAreaField('about', validators = [Length(min = 0, max = 1000)])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra conditions:
            challenge name must be unique
            challenge name must be changed
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        name = Challenge.query.filter_by(name = self.name.data).first()
        if name is not None:
            self.name.errors.append('A challenge with this name already exists. Please use a new one.')
            return False
        return True


class Update_Score(Form):
    '''Form to update the score for a user
    Parent: flask.ext.wtf.Form
    Attributes:
        userchoices - the list of users to choose from
        user - the field to choose a user, choices are userchoices
        challenge - the challenge selection list
        points - the number of points awarded to the user for the challenge, required
        submit - the submit field button
    '''
    userchoices = get_sorted_userlist()
    user = SelectField('user', choices = userchoices)
    challenge = SelectField('challenge', choices =[])
    points = IntegerField('points', validators = [DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Returns: True on sucessful validation, False when validation fails
        '''
        return Form.validate(self)


class Add_Subscriber(Form):
    '''Form add subscribers to the newsletter
    Parent: flask.ext.wtf.Form
    Attributes:
        users - users to add to the newsletter distribution list
                (newline separated), required
        submit - the submit field button
    '''
    users = TextAreaField('users', validators= [DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra condition:
            the user must have an RIT email address
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        users = self.users.data.split('\n')
        for user in users:
            if not re.search('\w{2,3}\d{4}@.*rit\.edu', user):
                self.users.errors.append('Invalid username')
                return False
        return True


class Permission_User(Form):
    '''Form to change the permissions for users
    Parent: flask.ext.wtf.Form
    Attributes:
        userchoices - the list of users to choose from
        rolechoices - the list of user roles to choose from
        user - the form field for user
        position - the form field for the chosen user's new position
        submit - the submit field button
    '''
    userchoices = get_sorted_userlist()
    rolechoices = [ (USER_ROLES[x], x) for x in USER_ROLES ]
    user = SelectField('user', choices = userchoices)
    role = SelectField('role', choices = rolechoices)
    position = TextField('position')
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Returns: True on sucessful validation, False when validation fails
        '''
        return Form.validate(self)


class CKTextAreaWidget(widgets.TextArea):
    '''Fancy text editor widget
    Parent: wtforms.widgets.TextArea
    '''
    def __call__(self, field, **kwargs):
        '''Make the class of the widget ckeditor so the input box is replaced
        with CKEditor
        Returns: the result of the parent __call__ function
        '''
        if kwargs.get('class'):
            kwargs['class'] += " ckeditor"
        else:
            kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    '''Fancy text editor field
    Parent: wtforms.fields.TextAreaField
    Attribute:
        widget - the CKTextAreaWidget to use for this text area
    '''
    widget = CKTextAreaWidget()


class Send_Newsletter(Form):
    '''Form to send the newsletter to subscribers
    Parent: flask.ext.wtf.Form
    Attributes:
        default - the default media list
        subject - the subject line of the newsletter, required
        body - the compose text area using ckeditor, required, default is at
               base_newsletter.html
        supported_socialmedia - the places supported by the site
        choices - the media choices
        media - the form field for the media checkboxes
        submit - the submit field button
    '''
    default = DEFAULT_MEDIA
    subject = TextField('subject', validators = [DataRequired()], default="RC3 Newsletter")
    body = CKTextAreaField('body', validators=[DataRequired()], default=BASE_NEWSLETTER)
    supported_socialmedia=SOCIAL_MEDIA
    choices = [(x, x) for x in supported_socialmedia]
    media = SelectMultipleField('media', choices = choices, option_widget= widgets.CheckboxInput())
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)


class Add_Presentation(Form):
    '''Form to add a presentation to the site
    Parent: flask.ext.wtf.Form
    Attributes:
        weeks - list of weeks in the semester
        week - form field to select the week of the presentation
        name - the form field for the name of presentation
        link - the form field for the link to the presentation
        submit - the submit field button
    '''
    weeks = [ (x, "Week {}".format(x)) for x in range(1, 16)]
    week = SelectField('week', choices=weeks, coerce=int)
    name = TextField('name', validators=[DataRequired()])
    link = TextField('link', validators=[DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra condition:
            The url must be a google presentation
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        if not re.search('https://.*google.com/./.*/presentation/.*embed.*',
                         self.link.data) and \
           not re.search("https://.*google.com/presentation/./.*/embed.*",
                         self.link.data):
            return False
        return True


class EditPresentation(Form):
    '''Form to edit existing presentations
    Parent: flask.ext.wtf.Form
    Attributes:
        pres - the presentation to edit
        name - the form field for the name of presentation
        link - the form field for the link to the presentation
        submit - the submit field button
    '''
    pres = SelectField('pres', choices=[], coerce=int)
    name = TextField('name')
    link = TextField('link')
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra condition:
            the presentation must be a google presentation
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        if not re.search('https://.*google.com/./.*/presentation/.*embed.*',
                         self.link.data) and \
           not re.search("https://.*google.com/presentation/./.*/embed.*",
                         self.link.data):
            return False
        return True

class DeletePresentation(Form):
    '''Form to delete an existing presentation
    Parent: flask.ext.wtf.Form
    Attributes:
        pres - the presentation to edit
        confirm - checkbox to confirm deletion
        submit - the submit field button
    '''
    pres = SelectField('pres', choices=[], coerce=int)
    confirm = BooleanField('confirm', widget= widgets.CheckboxInput())
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra condition:
            the deleteion must be confirmed
        Returns: True on sucessful validation, False when validation fails
        '''
        if not Form.validate(self):
            return False
        if not self.confirm.data:
            return False
        return True

class AddNewsArticle(Form):
    '''Form to add a news article
    Parent: flask.ext.wtf.Form
    Attributes:
        title - the form field for the title of the news article, required
        description - the form field for describing the article, required,
                      max = 10, min = 1000
        link - the form field for the link to the article, required
        date - the form field for the date the article was added, required
        submit - the submit field button
    '''
    title = TextField('title', validators = [DataRequired()])
    description = TextAreaField('body', validators = [Length(min = 10, max = 1000)])
    link = TextField('site', validators = [DataRequired()])
    date = DateField('date', validators = [DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Returns: True on sucessful validation, False when validation fails
        '''
        return Form.validate(self)

class AddAllowedUser(Form):
    '''Add a non-rit user
    Parent: flask.ext.wtf.Form
    Attributes:
        email - the form field for the email address to allow, required
        ban - the options to ban the user email
        submit - the submit field button
    '''
    email = TextField('email', validators=[DataRequired()])
    ban = RadioField('ban', choices=[('1', 'Yes'), ('0', 'No')], default='0')
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        '''validate the form input
        Extra condition:
            there must be an @ in the email address entered
        Returns: True on sucessful validation, False when validation fails
        '''
        if "@" in self.email.data:
            return True
        return False


'''''''''''''''''''''''
Blog forms
'''''''''''''''''''''''
class Add_Post(Form):
    '''Form to add a post to the blog
    Parent: flask.ext.wtf.Form
    Attributes:
        title - the form field for the title of the post, required
        body - the form field for the body of the post, required
        submit - the submit field button
    '''
    title = TextField('subject', validators = [DataRequired()], default="")
    body = CKTextAreaField('body', validators=[DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init__(self, *args, **kwargs)


class Edit_Post(Form):
    '''Form to edit an existing post on the blog
    Parent: flask.ext.wtf.Form
    Attributes:
        title - the form field for the title of the post to edit, required
        body - the form field for the body of the post to edit, required
        submit - the submit field button
    '''
    title = TextField('subject', validators = [DataRequired()])
    body = CKTextAreaField('body', validators=[DataRequired()])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        '''initializes the class, uses parent's __init__'''
        Form.__init(self, *args, **kwargs)
