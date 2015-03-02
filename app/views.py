# -*- coding: utf-8 -*-
"""
    hackathonranks.views
    ~~~~~~~~~~~~~~~~~~~~

    Html views.
"""


import base64
import pytz
import requests

from app import auth, utils
from app.forms import HackathonForm
from app.models import db, User, Hackathon, Rank

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
    context = {
        'hackathons': Hackathon.query.all(),
    }
    return render_template('index.html', **context)


@blueprint.route('/login')
def login():
    scope = 'email,read_logged_time'
    state = {
        'c':g.csrftoken,
        'n': '/',
    }
    params = {
        'response_type': 'code',
        'client_id': app.config['WAKATIME_CLIENT_ID'],
        'redirect_uri': app.config['WAKATIME_REDIRECT_URI'],
        'state': json.dumps(state),
        'scope': scope,
    }
    url = 'https://wakatime.com/oauth/authorize'
    return redirect(utils.add_params_to_url(url, params))


@blueprint.route('/login/callback')
def login_callback():

    # validate csrf token from state
    state = utils.get_and_validate_state(request)
    if not state:
        app.logger.error('Invalid state.')
        abort(403)

    code = request.args.get('code')
    error = request.args.get('error')
    if not code or error:
        app.logger.error('Error: {0}'.format(error))
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
        'User-Agent': app.config['USER_AGENT'],
    }
    access_url = 'https://wakatime.com/oauth/token'
    response = requests.post(access_url, data=data, headers=headers)

    app.logger.debug(response.status_code)
    app.logger.debug(response.text)

    if response.status_code != 200:
        app.logger.error(response.text)
        abort(500)

    access_token = response.json().get('access_token')
    scopes = response.json().get('scope')

    app.logger.debug(access_token)
    app.logger.debug(scopes)

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Basic {0}'.format(base64.b64encode(access_token)),
        'User-Agent': app.config['USER_AGENT'],
    }
    response = requests.get('https://wakatime.com/api/v1/users/current?token=' + access_token, headers=headers)

    app.logger.debug(response.status_code)
    app.logger.debug(response.text)

    if response.status_code != 200:
        app.logger.error(response.text)
        abort(400)

    if response.json()['data']['username']:
        profile_url = 'https://wakatime.com/@' + response.json()['data']['username']
    else:
        profile_url = 'https://wakatime.com/' + response.json()['data']['id']
    defaults = {
        'wakatime_token': access_token,
        'email': response.json()['data']['email'],
        'avatar_url': response.json()['data']['photo'],
        'full_name': response.json()['data']['full_name'],
        'username': response.json()['data']['username'],
        'profile_url': profile_url,
    }
    user = User.get_or_create(defaults=defaults, wakatime_id=response.json()['data']['id'])
    user.set_columns(**defaults)
    db.session.commit()

    auth.login_user(user)

    if auth.is_safe_url(state.get('n')):
        return redirect(state.get('n'))
    return redirect('/')


@blueprint.route('/hackathon/<path:hackathon_name>')
def hackathon(hackathon_name):
    hackathon = Hackathon.query.filter_by(name=hackathon_name).first()
    if hackathon is None:
        abort(404)

    context = {
        'hackathon': hackathon,
        'hackers': hackathon.ranks.all(),
    }
    return render_template('hackathon.html', **context)


@blueprint.route('/hackathon/<path:hackathon_name>/join')
@auth.login_required
def hackathon_join(hackathon_name):
    hackathon = Hackathon.query.filter_by(name=hackathon_name).first()
    if hackathon is None:
        abort(404)

    headers = {
        'Accept': 'application/json',
        'User-Agent': app.config['USER_AGENT'],
    }
    timezone = pytz.timezone(hackathon.timezone)
    params = {
        'start': hackathon.coding_starts_at.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%m/%d/%Y'),
        'end': hackathon.coding_ends_at.replace(tzinfo=pytz.utc).astimezone(timezone).strftime('%m/%d/%Y'),
        'token': app.current_user.wakatime_token,
    }
    response = requests.get('https://wakatime.com/api/v1/users/current/summaries', headers=headers, params=params)

    app.logger.debug(response.status_code)
    app.logger.debug(response.text)

    if response.status_code != 200:
        abort(400)

    total_seconds = 0
    for day in response.json()['data']:
        total_seconds += day['grand_total']['total_seconds']

    defaults = {
        'total_seconds': total_seconds,
    }
    rank = Rank.get_or_create(defaults=defaults, hackathon_id=hackathon.id, user_id=app.current_user.id)
    rank.set_columns(**defaults)
    db.session.commit()

    context = {
        'hackathon': hackathon,
    }
    return render_template('hackathon.html', **context)


@blueprint.route('/new/hackathon', methods=['GET', 'POST'])
@auth.login_required
def create_hackathon():
    form = HackathonForm(request.form)
    if request.method == 'POST' and form.validate():
        hackathon = Hackathon(admin_id=app.current_user.id, **form.data)
        db.session.add(hackathon)
        db.session.commit()
        return redirect('/hackathon/'+hackathon.name)
    context = {
        'form': form,
    }
    return render_template('create_hackathon.html', **context)
