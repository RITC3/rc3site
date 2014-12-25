from app import db
from hashlib import md5
from config import USER_ROLES, CURRENT_SEMESTER
from sqlalchemy import desc

class User(db.Model):
    """docstring for User"""
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
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def get_score(self, challenge='all'):
        if challenge is 'all':
            total = 0
            for s in self.scores:
                total+= s.points
        else:
            for s in self.scores:
                if s.challenge is challenge:
                    total = s.points
        return total

    def last_seen_print(self):
        return self.last_seen.strftime('%A, %B %d %Y %I:%M%p')

    def avatar(self, size):
        return "http://www.gravatar.com/avatar/{0}?d=mm&s={1}".format(md5(self.email).hexdigest(), str(size))

    # @staticmethod
    # def make_unique_nickname(nickname):
    #     if User.query.filter_by(nickname = nickname).first() == None:
    #         return nickname
    #     version = 2
    #     while True:
    #         new_nickname = nickname + str(version)
    #         if User.query.filter_by(nickname = new_nickname).first() == None:
    #             break
    #         version += 1
    #     return new_nickname

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    def __eq__(self, other):
        return self.get_score() == other.get_score()

    def __lt__(self, other):
        return self.get_score() < other.get_score()

    def __cmp__(self, other):
        try :
            if self.get_score() > other.get_score():
                return -1
            if self.get_score() < other.get_score():
                return 1
        except :
            return -1

class Post(db.Model):
    """docstring for Post"""
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)

class Challenge(db.Model):
    """docstring for Challenge"""
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique= True)
    about = db.Column(db.String(1000), index = True)
    date = db.Column(db.DateTime)
    scores = db.relationship('Score', backref = 'challenge', lazy = 'dynamic')

    def total_users(self):
        # This is really ineffecient, but it's 2:23AM and I don't care
        total = 0
        for score in self.scores:
            total+=1
        return total

    def get_users(self):
        users = []
        sorted_scores = sorted(self.scores, key=lambda score: score.points, reverse = True)

        for score in sorted_scores:
            user = User.query.filter_by(id=score.user_id).first()
            users.append(user)
        return users



    def __repr__(self):
        return '<Challenge %r>' % (self.name)

class Score(db.Model):
    """docstring for Score"""
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'))
    points = db.Column(db.Integer, default = 0)

    def __repr__(self):
        return '<Score %r : %r>' % (self.user_id, self.points)

    def __cmp__(self, other):
        try :
            if self.points > other.points:
                return -1
            if self.points < other.points:
                return 1
        except :
            return -1

class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    semester_id = db.Column(db.Integer, default = CURRENT_SEMESTER)
    name = db.Column(db.String(100))
    week = db.Column(db.SmallInteger)
    link = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime)

    def __repr__(self):
        return '<Presentation Week {}: {}>'.format(self.pres_week, self.pres_name)
