from app import db
from hashlib import md5
from config import USER_ROLES

class User(db.Model):
    '''The database model for users
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        nickname - the nickname for the user
        username - the username (rit DCE or first 10 of the user email) for the user
        email - the email address of the user
        role - the role of the user, see USER_ROLES in config.py
        postition - the position name for the user
        major - the major of study for the user
        newsletter - user preference for newsletter receipt
        about_me - the user bio
        last_seen - the last time the user was on the site
        posts - the posts that the user has posted
        scores - the individual scores that the user has earned for challenges
    '''
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), index = True)
    username = db.Column(db.String(10), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = USER_ROLES['user'])
    position = db.Column(db.String(64), index = True)
    major = db.Column(db.String(64), index = True)
    newsletter = db.Column(db.Integer, default = 1)
    about_me = db.Column(db.String(300))
    last_seen = db.Column(db.DateTime)
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
    scores = db.relationship('Score', backref = 'user', lazy = 'dynamic')

    def is_authenticated(self):
        '''Is the user authenticated
        Returns: True, always
        '''
        return True

    def is_active(self):
        '''Is the user active?
        Returns: True, always
        '''
        return True

    def is_anonymous(self):
        '''Is the user anonymous?
        Returns: False, always
        '''
        return False

    def get_id(self):
        '''Gets the user id
        Returns: The user id as unicode
        '''
        return unicode(self.id)

    def is_admin(self):
        '''Is the user an admin?
        Returns: True if the user is an admin, False otherwise
        '''
        if self.role is USER_ROLES['admin']:
            return True
        return False

    '''This function should be simplified...'''
    def get_score(self, challenge='all', semester='all'):
        '''Get the score for the user
        args:
            challenge - the challenge object to get the score for
            semester - the semester object to get the score for
        Returns: the total number of points for the user for the specified
                 semester and challenge
        Note: This function should be simplified
        '''
        total = 0
        if semester is 'all':
            if challenge is 'all':
                for s in self.scores:
                        total += s.points
            else:
                for s in self.scores:
                    if s.challenge is challenge:
                            total = s.points
        else:
            if challenge is 'all':
                for s in self.scores:
                    if s.semester == semester:
                        total += s.points
            else:
                for s in self.scores:
                    if s.challenge is challenge and s.semester == semester:
                            total = s.points
        return total

    def last_seen_print(self):
        '''Generate a date string with the user's last seen time
        Returns: The date string
        '''
        return self.last_seen.strftime('%A, %B %d %Y %I:%M%p')

    def avatar(self, size):
        '''Generates the gravatar URL for the user
        arg:
            size - the size of the gravatar requested
        Returns: The URL for the user's gravatar
        '''
        return "http://www.gravatar.com/avatar/{0}?d=mm&s={1}".format(md5(self.email).hexdigest(), str(size))

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<User %r>' % (self.nickname)

    def __eq__(self, other):
        '''The equals comparison, compares user scores
        arg:
            other - the other user to compare
        Returns: True if user scores are equal, False otherwise
        Note: Broken
        '''
        return self.get_score() == other.get_score()

    def __lt__(self, other):
        '''The less than comparison, compares user scores
        arg:
            other - the other user to compare
        Returns: True if this user's score is less than the other's, False otherwise
        Note: Broken
        '''
        return self.get_score() < other.get_score()

    def __cmp__(self, other):
        '''Compares user scores
        arg:
            other - the other user to compare
        Returns: 1 if this user's score is less than the other user's
                 -1 if this user's score is greater than the other user's
                 Nothing otherwise
        Note: Broken
        '''
        try :
            if self.get_score() > other.get_score():
                return -1
            if self.get_score() < other.get_score():
                return 1
        except :
            return -1

class Semester(db.Model):
    '''The database model for semesters
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        name - the space separated name of the semester, for display
        lname - the one word name of the semester, for links
        current - indicates whether the semester is the current one or not
        Note: ONLY ONE semester should be marked current
    '''
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20), unique = True, index = True)
    lname = db.Column(db.String(20), index = True, unique = True)
    current = db.Column(db.Boolean, default = True)

    def __init__(self, current, name):
        '''Initializes the object on create
        args:
            current - indicate whether this is the current semester or not
            name - the space separated name of the semester
        '''
        self.current = current
        self.name = name
        self.lname = self.name.replace(" ", "")

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<Semester: {}>'.format(self.name)

    def __cmp__(self, other):
        '''Compares semesters by id
        arg:
            other - the semester to compare to this one
        Returns: 0 if the semesters are the same
                 1 if this semester is greater than the other semester
                 -1 if this semester is less than the other semester
        Note: This function relies on the assumption that semesters are added
              chronologically
        '''
        try:
            if self.id == other.id:
                return 0
            if self.id > other.id:
                return 1
            if self.id < other.id:
                return -1
        except:
            return -1

class Post(db.Model):
    '''The database model for blog posts
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        title - the title of the blog post
        body - the html body of the blog post
        timestamp - the time the blog post was created
        user_id - the id of the User that created the post
    '''
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(50))
    body = db.Column(db.String(25000))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<Post %r>' % (self.body)

class Challenge(db.Model):
    '''The database model for challenges
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        name - the name of the challenge
        about - the description of the challenge
        date - the date that the challenge was posted on
        scores - the scores associated with the challenge, up to one per user?
        semester_id - the foreign key for the semester that the challenge was
                      given in
        semester - the semester object associated with the challenge's semester_id
    '''
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique= True)
    about = db.Column(db.String(1000), index = True)
    date = db.Column(db.DateTime)
    scores = db.relationship('Score', backref = 'challenge', lazy = 'dynamic')
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    semester = db.relationship("Semester")

    def total_users(self):
        '''Gets the total number of users that participated in the challenge
        Returns: the number of users that participated
        Note: This is inefficient
        '''
        total = 0
        for score in self.scores:
            total+=1
        return total

    def get_users(self):
        '''Gets a lits of all users that participated in this challenge
        Returns: a list of users that participated
        '''
        users = []
        sorted_scores = sorted(self.scores, key=lambda score: score.points, reverse = True)

        for score in sorted_scores:
            user = User.query.filter_by(id=score.user_id).first()
            users.append(user)
        return users

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<Challenge %r>' % (self.name)

class Score(db.Model):
    '''The database model for scores, relates challenges to users
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        user_id - the user associated with the score
        challenge_id - the challenge associated with the score
        points - number of points associated with the score
        semester_id - the foreign key for the semester that the score was
                      given in
        semester - the semester object associated with the score's semester_id
    '''
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'))
    points = db.Column(db.Integer, default = 0)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    semester = db.relationship("Semester")

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<Score %r : %r>' % (self.user_id, self.points)

    def __cmp__(self, other):
        '''Compares semesters by id
        arg:
            other - the score to compare to this one
        Returns: 0 if the scores are the same
                 -1 if this score is greater than the other score
                 1 if this score is less than the other score
        Note: This might be wrong, contradicts the logic in the other __cmp__
        '''
        try :
            if self.points > other.points:
                return -1
            if self.points < other.points:
                return 1
        except :
            return -1

class Presentation(db.Model):
    '''The database model for scores, relates challenges to users
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        name - the name of the presentation
        week - the week number for the presentation (1-15)
        link - the Google Slideshow presentation link for the presentation
        timestamp - the date that the presentation was given
        semester_id - the foreign key for the semester that the presentation was
                      given in
        semester - the semester object associated with the presentation's semester_id
    '''
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), index = True)
    week = db.Column(db.SmallInteger, index = True)
    link = db.Column(db.String(300), index = True)
    timestamp = db.Column(db.DateTime)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    semester = db.relationship("Semester")

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<Presentation Week {}: {}>'.format(self.pres_week, self.pres_name)

class News(db.Model):
    '''The database model for news posts
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        title - the tagline for the news post
        description - the short summary of the news post
        link - the link to the original article of the news post
        date - the date the newspost was posted
        semester_id - the foreign key for the semester that the challenge was
                      given in
        semester - the semester object associated with the challenge's semester_id
    '''
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    link = db.Column(db.String(300))
    date = db.Column(db.Date)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    semester = db.relationship("Semester")

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<News Item: {}>'.format(self.article)

class AllowedUser(db.Model):
    '''Database model for explicitly allowed users outside RIT (or banning users)
    Parent: flask.ext.sqlalchemy.Model
    Attributes:
        id - primary key for the table
        email - the email address of the user to allow (or ban)
        ban - bans the user from the site if True, allows them if False
    '''
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), index = True, unique = True)
    ban = db.Column(db.Boolean, default = False)

    def __repr__(self):
        '''Prints when the object is called directly
        Returns: A string to describe the object
        '''
        return '<AllowedUser: {}>'.format(self.email)
