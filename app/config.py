# -*- coding: utf-8 -*-
"""
    hackathonranks.config
    ~~~~~~~~~~~~~~~~~~~~~

    Configurations.
"""


import os
import socket
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
HOSTNAME = socket.gethostname()
if HOSTNAME.startswith('hackathon'):
    DEV = False
else:
    DEV = True

DEBUG = True if DEV else False

# Import secrets
if not DEV:
    from secrets import *
else:
    from secrets_dev import *

# Flask-Login
REMEMBER_COOKIE_NAME = 'remember_token'
REMEMBER_COOKIE_DURATION = timedelta(weeks=4)
REMEMBER_COOKIE_DOMAIN = '.'+HOSTNAME
REMEMBER_COOKIE_SECURE = False if DEV else True
REMEMBER_COOKIE_HTTPONLY = True

# Flask-SeaSurf CSRF
CSRF_DISABLE = False
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_TIMEOUT = timedelta(days=7)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False if DEV else True

# Flask-WTF
CSRF_ENABLED = False

# Flask
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False if DEV else True

# Static Files
STATIC_FOLDER = os.path.abspath(os.path.join(BASE_DIR, 'app/static'))
COMPRESSOR_DEBUG = DEBUG
COMPRESSOR_OFFLINE_COMPRESS = not DEBUG
COMPRESSOR_OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, 'app/static/sdist'))
COMPRESSOR_STATIC_PREFIX = '/static/sdist'

USER_AGENT = 'hackathonrank/1.0.0'

ALEMBIC_CONFIG = os.path.join(BASE_DIR, 'alembic.ini')
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'hackathonrank'
DB_SSL = 'disable'
if DEV:
    DB_USERNAME = 'hackathonrank'
    DB_PASSWORD = 'hackathonrank'
    DB_HOST = 'localhost'
    DB_PORT = 5432
    DB_SSL = 'disable'
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pw}@{host}:{port}/{database}?sslmode={ssl}'.format(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USERNAME,
    pw=DB_PASSWORD,
    ssl=DB_SSL,
)
