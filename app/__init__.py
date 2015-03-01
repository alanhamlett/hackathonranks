# -*- coding: utf-8 -*-
"""
    hackathonranks
    ~~~~~~~~~~~~~~

    The app.
"""

from datetime import datetime

from flask import Flask, g, render_template
from flask.ext.seasurf import SeaSurf


# Flask App Setup
app = Flask(__name__)
app.config.from_object('app.config')
app.secret_key = app.config['SECRET_KEY']
app.url_map.strict_slashes = False
app.jinja_env.globals.update(
    STATIC_URL=app.static_url_path+'/',
)

# Logging
from app import logger

# JSON Serialization
from app.json import CustomJSONEncoder, CustomJSONDecoder
app.json_encoder = CustomJSONEncoder
app.json_decoder = CustomJSONDecoder

# CSRF Protection Setup
csrf = SeaSurf(app)

# Flask-Login Extension and Auth Utils
from app import auth
from flask.ext.login import current_user
app.current_user = current_user

# Html Views
from app.views import blueprint as views
app.register_blueprint(views)

# Compress static files
from jac.contrib.flask import JAC
jac = JAC(app)
