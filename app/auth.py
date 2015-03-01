# -*- coding: utf-8 -*-
"""
    hackathonranks.auth
    ~~~~~~~~~~~~~~~~~~~

    Authentication using Flask-Login.
"""


from functools import wraps
from urlparse import urlparse, urljoin

from app import app
from app.compat import u
#from app.models import User

from flask import redirect, request, url_for
from flask.ext.login import LoginManager, login_user, logout_user, login_required


# require some imports for other modules to use
assert login_required
assert login_user
assert logout_user


# try importing uwsgi, which will fail if we are not in app context
# for example when running command line scripts or alembic
class Uwsgi(object):
    def set_logvar(*args, **kwargs):
        pass
try:
    import uwsgi
except ImportError:
    uwsgi = Uwsgi()

login_manager = LoginManager()
login_manager.setup_app(app)


@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id, active=True).first()
    if user:
        uwsgi.set_logvar('user_id', str(user.id))
        uwsgi.set_logvar('user_email', u(user.email).encode('ascii', errors='backslashreplace'))
    else:
        uwsgi.set_logvar('user_id', '')
        uwsgi.set_logvar('user_email', '')
    return user


def get_next_url():
    next_url = request.args.get('next')
    if not next_url or not is_safe_url(next_url):
        next_url = url_for('views.index')
    return next_url


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def redirect_back(url):
    if not url or not is_safe_url(url):
        url = url_for('views.index')
    return redirect(url)


def login_not_allowed(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if app.current_user.is_authenticated():
            return redirect(url_for('views.index'))
        return f(*args, **kwargs)
    return decorated
