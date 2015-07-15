from flask import render_template, flash, redirect, url_for, request, g, Blueprint
from flask.ext.login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Post, User
from app.forms import CKTextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask.ext.admin import AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from config import USER_ROLES
from sqlalchemy import desc

blog = Blueprint('blog', __name__, subdomain='blog', static_folder="../static")

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
    posts = Post.query.order_by(desc(Post.timestamp))
    return render_template('blog/index.html', posts=posts)

@blog.route('/post/<num>')
def post(num):
    post = Post.query.filter_by(id=num).first()
    if post is None:
        return render_template('404.html'), 404
    return render_template('blog/single_post.html', post=post)

class ProtectedBaseView(BaseView):
    def is_accessible(self):
        if current_user.is_authenticated() and current_user.role == 1:
            return True
        return False

    def _handle_view(self, name, **kwargs):
            if not self.is_accessible():
                flash("You don't have permission to go there", category="warning")
                return redirect(url_for('main.index'))

class ProtectedIndexView(AdminIndexView, ProtectedBaseView):
    pass

class ProtectedModelView(ModelView, ProtectedBaseView):
    pass

class ProtectedFileAdmin(FileAdmin, ProtectedBaseView):
    pass

class PostModelView(ProtectedModelView):
    edit_template = 'blog/admin/edit_add_post.html'
    create_template = 'blog/admin/edit_add_post.html'
    form_overrides = dict(body=CKTextAreaField)
    column_formatters=dict(body=lambda view, context, model, name: ' '.join(model.body.split(" ")[:50]))
    column_default_sort = ('id', True)
    form_args = dict(
        author=dict(
            default=User.query.filter_by(role=USER_ROLES['admin']).first(),
            query_factory=lambda: [current_user]
        ))

    def __init__(self):
        super(PostModelView, self).__init__(Post, db.session)
