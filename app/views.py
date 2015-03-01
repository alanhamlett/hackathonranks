# -*- coding: utf-8 -*-
"""
    hackathonranks.views
    ~~~~~~~~~~~~~~~~~~~~

    Html views.
"""

import pytz
import requests
from firebase import firebase

from app import (
    utils,
)
from app.utils import add_params_to_url, get_and_validate_state

from flask import current_app as app
from flask import (
    abort,
    Blueprint,
    g,
    json,
    render_template,
    request,
    redirect,
)


blueprint = Blueprint('views', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')


@blueprint.route('/login')
def login():
    scope = 'email,read_logged_time'
    state = {
        'c':g.csrftoken,
    }
    params = {
        'response_type': 'code',
        'client_id': app.config['WAKATIME_CLIENT_ID'],
        'redirect_uri': app.config['WAKATIME_REDIRECT_URI'],
        'state': json.dumps(state),
        'scope': scope,
    }
    url = 'https://wakatime.com/oauth/authorize?response_type=code'
    return redirect(add_params_to_url(url, params))


@blueprint.route('/login/callback')
def login_callback():

    # validate csrf token from state
    state = get_and_validate_state(request)
    if not state:
        abort(403)

    code = request.args.get('code')
    error = request.args.get('error')
    if not code or error:
        abort(400)

    # get access token
    data = {
        'code': code,
        'client_id': app.config['WAKATIME_CLIENT_ID'],
        'client_secret': app.config['WAKATIME_SECRET'],
        'redirect_uri': app.config['WAKATIME_REDIRECT_URI'],
        'grant_type': 'authorization_code',
    }
    headers = {
        'Accept': 'application/json',
    }
    access_url = 'https://wakatime.com/oauth/token'
    response = requests.post(access_url, data=data, headers=headers)

    app.logger.debug(response.status_code)
    app.logger.debug(response.text)

    if response.status_code != 200:
        abort(500)

    access_token = response.json().get('access_token')
    scopes = response.json().get('scope')

    headers = {
        'Accept': 'application/json',
    }
    response = requests.get('https://wakatime.com/api/v1/users/current', headers=headers)
    if not response:
        abort(400)

    if utils.is_safe_url(state.get('n')):
        return redirect(state.get('n'))
    return redirect('/')
