from flask import render_template, flash, redirect, session, url_for, request, g, abort, Blueprint
from flask.ext.login import login_required, current_user
from datetime import datetime
from app import app, db
from app.models import Post
from app.forms import Add_Post

blog = Blueprint('blog', __name__, subdomain='blog')

def is_admin():
    if g.user.role == 1:
        return True
    else:
        return False

@blog.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@blog.route('/')
@blog.route('/index')
def index():
    posts = Post.query.all()
    return render_template('blog/index.html', posts=posts)


@blog.route('/admin', methods = ['GET', 'POST'])
@login_required
def admin():
    if not is_admin():
        return render_template('404.html'), 404
    posts = Post.query.all()
    add_post = Add_Post()
    if request.form.get('submit', None) == 'Add Post':
        if add_post.validate_on_submit():
            post = Post(title=add_post.data['title'], body=add_post.data['body'], user_id=g.user.id)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('blog.admin'))
        else:
            flash("Invalid post")

    BLOG_FORMS = {'add_post':add_post}
    return render_template('blog/admin.html', title="Blog Admin", BLOG_FORMS=BLOG_FORMS, posts=posts)

@blog.route('/post/<num>')
def post(num):
    post = Post.query.filter_by(id=num).first()
    if post is None:
        return render_template('404.html'), 404
    return render_template('blog/single_post.html', post=post)
