import re
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, SelectField, IntegerField, SubmitField, widgets, SelectMultipleField
from wtforms.fields import DateField
from wtforms.validators import Required, Length, DataRequired
from datetime import datetime
from app.models import User, Challenge
from config import SOCIAL_MEDIA, DEFAULT_MEDIA, USER_ROLES

def get_sorted_userlist():
    userchoices = []
    users = User.query.all()
    users.sort(key=lambda x: x.nickname.lower())
    for user in users:
        if user.nickname == user.username:
            userchoices.append((user.id, "{0}".format(user.username)))
        else:
            userchoices.append((user.id, "{0} - {1}".format(user.nickname,user.username)))
    return userchoices

class MultiCheckboxField(SelectMultipleField):
    """docstring for MultiCheckboxField"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
    def __call__(self, field, **kwargs):
        if getattr(field, 'checked', field.data):
            kwargs['checked'] = True
            return super(CheckboxInput, self).__call__(field, **kwargs)

class LoginForm(Form):
    openid = TextField('openid', validators = [(DataRequired())])
    remember_me = BooleanField('remember_me', default = False)

class EditForm(Form):
    nickname = TextField('nickname', validators = [DataRequired()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 300)])
    major = TextField('major', validators = [Length(min = 0, max = 64)])
    newsletter = BooleanField('newsletter', widget= widgets.CheckboxInput())

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname = self.nickname.data).first()
        if user != None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True

class Edit_Challenge(Form):
    name = TextField('name', validators = [DataRequired(), Length(min = 1, max = 64)])
    date = DateField('date', validators = [DataRequired()])
    about = TextAreaField('about', validators = [Length(min = 0, max = 1000)])
    submit = SubmitField('submit')

    def __init__(self, original_name, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_name = original_name

    def validate(self):
        if not Form.validate(self):
            return False
        name = Challenge.query.filter_by(name = self.name.data).first()
        if self.name.data == self.original_name:
            return True
        if name != None:
            self.name.errors.append('A challenge with this name already exists. Please use a new one.')
            return False
        return True


class ContactUs(Form):
    name = TextField('name', validators = [DataRequired()])
    email = TextField('email', validators = [Length(min = 6, max = 140)])
    body = TextAreaField('body', validators = [Length(min = 1, max = 1000)])

    def validate(self):
        if not Form.validate(self):
            return False
        return True

class Create_Challenge(Form):
    """docstring for Create_Challenge"""
    name = TextField('name', validators = [DataRequired(), Length(min = 1, max = 64)])
    date = DateField('date', validators = [DataRequired()], default = datetime.now())
    about = TextAreaField('about', validators = [Length(min = 0, max = 1000)])
    submit = SubmitField('submit')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        name = Challenge.query.filter_by(name = self.name.data).first()
        if name != None:
            self.name.errors.append('A challenge with this name already exists. Please use a new one.')
            return False
        return True

class Update_Score(Form):
    """docstring for Update_Score"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
    userchoices = get_sorted_userlist()
    challengechoices = []
    challenges = Challenge.query.all()
    for chall in challenges:
        challengechoices.append((chall.id, chall.name))
    user = SelectField('user', choices = userchoices)
    challenge = SelectField('challenge', choices = challengechoices)
    points = IntegerField('points', validators = [DataRequired()])
    submit = SubmitField('submit')

    def validate(self):
        return True

class Add_Subscriber(Form):
    """docstring for Add_Subscriber"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    users = TextAreaField('users', validators= [DataRequired()])
    submit = SubmitField('submit')

    def validate(self):
        if not Form.validate(self):
            return False
        users = self.users.data.split('\n')
        for user in users:
            if not re.search('\w{2,3}\d{4}@.*rit\.edu', user):
                self.users.errors.append('Invalid username')
                return False
        return True

class Permission_User(Form):
    """docstring for Update_Score"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    userchoices = get_sorted_userlist()
    rolechoices = []
    for key in USER_ROLES:
        rolechoices.append((USER_ROLES[key],key))
    user = SelectField('user', choices = userchoices)
    role = SelectField('role', choices = rolechoices)
    position = TextField('points')
    submit = SubmitField('submit')

    def validate(self):
        return True

class Send_Newsletter(Form):
    """docstring for Send_Newsletter"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    default = DEFAULT_MEDIA
    subject = TextField('subject', validators = [DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    supported_socialmedia=SOCIAL_MEDIA
    choices = [(x,x) for x in supported_socialmedia]
    media = SelectMultipleField('media', choices = choices, option_widget= widgets.CheckboxInput())
    # media = MultiCheckboxField('media', choices=choices)
    submit = SubmitField('submit')

