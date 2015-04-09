import re
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, SelectField, IntegerField, SubmitField, widgets, SelectMultipleField, RadioField
from wtforms.fields import DateField, TextAreaField
from wtforms.validators import Required, Length, DataRequired
from datetime import datetime
from app.models import *
from config import SOCIAL_MEDIA, DEFAULT_MEDIA, USER_ROLES, BASE_NEWSLETTER

def get_sorted_userlist():
    userchoices = []
    users = User.query.all()
    users.sort(key=lambda user: user.nickname.lower())
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
    user = SelectField('user', choices = userchoices)
    challenge = SelectField('challenge', choices =[])
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

"""Fancy text editor"""
class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

class Send_Newsletter(Form):
    """docstring for Send_Newsletter"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    default = DEFAULT_MEDIA
    subject = TextField('subject', validators = [DataRequired()], default="RC3 Newsletter")
    body = CKTextAreaField('body', validators=[DataRequired()], default=BASE_NEWSLETTER)
    supported_socialmedia=SOCIAL_MEDIA
    choices = [(x,x) for x in supported_socialmedia]
    media = SelectMultipleField('media', choices = choices, option_widget= widgets.CheckboxInput())
    submit = SubmitField('submit')

class Add_Presentation(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    weeks = [ (x, "Week {}".format(x)) for x in range(1,16)]
    week = SelectField('week', choices=weeks, coerce=int)
    name = TextField('name', validators=[DataRequired()])
    link = TextField('link', validators=[DataRequired()])
    submit = SubmitField('submit')

    def validate(self):
        if not Form.validate(self):
            return False
        if not re.search('https://.*google.com/./.*/presentation/.*embed.*', self.link.data) and not re.search("https://.*google.com/presentation/./.*/embed.*", self.link.data):
            return False
        return True

class EditPresentation(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    pres = SelectField('pres', choices=[], coerce=int)
    name = TextField('name')
    link = TextField('link')
    submit = SubmitField('submit')

    def validate(self):
        if not Form.validate(self):
            return False
        if not re.search('https://.*google.com/./.*/presentation/.*embed.*', self.link.data) and not re.search("https://.*google.com/presentation/./.*/embed.*", self.link.data):
            return False
        return True

class DeletePresentation(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    pres = SelectField('pres', choices=[], coerce=int)
    confirm = BooleanField('confirm', widget= widgets.CheckboxInput())
    submit = SubmitField('submit')

    def validate(self):
        if self.confirm.data:
            return True
        return False

"""Adding a news article to newspage"""
class AddNewsArticle(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    title = TextField('title', validators = [DataRequired()])
    description = TextAreaField('body', validators = [Length(min = 10, max = 1000)])
    link = TextField('site', validators = [DataRequired()])
    date = DateField('date', validators = [DataRequired()])
    submit = SubmitField('submit')

    def validate(self):
        return True

"""Adding a non-rit user"""
class AddAllowedUser(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    email = TextField('email', validators=[DataRequired()])
    ban = RadioField('ban', choices=[('1', 'Yes'), ('0', 'No')], default='0')
    submit = SubmitField('submit')

    def validate(self):
        if "@" in self.email.data:
            return True
        return False

class Add_Post(Form):
    """docstring for Send_Newsletter"""
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    title = TextField('subject', validators = [DataRequired()], default="")
    body = CKTextAreaField('body', validators=[DataRequired()])
    submit = SubmitField('submit')

class Edit_Post(Form):
    def __init__(self, *args, **kwargs):
        Form.__init(self, *args, **kwargs)

    title = TextField('subject', validators = [DataRequired()])
    body = CKTextAreaField('body', validators=[DataRequired()])
    submit = SubmitField('submit')
