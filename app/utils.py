# -*- coding: utf-8 -*-
"""
    hackathonranks.utils
    ~~~~~~~~~~~~~~~~~~~~

    Utilities.
"""


import urllib
import urlparse

from flask import json, g

from app import app
from app.compat import u


def add_params_to_url(url, params):
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)


def get_and_validate_state(request):
    state = request.args.get('state')
    try:
        state = json.loads(state)
    except:
        state = {}
    if not isinstance(state, dict):
        app.logger.error('State is not a dict.')
        return None
    url_token = state.get('c')
    cookie_token = g.csrftoken
    if not cookie_token or u(url_token) != u(cookie_token):
        app.logger.error('State {0} does not match {1}'.format(u(url_token), u(cookie_token)))
        return None
    return state
