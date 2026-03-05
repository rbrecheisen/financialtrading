import base64
import json
import requests
from flask import Flask, redirect, request
from urllib.parse import urlencode
from pathlib import Path

app = Flask(__name__)

oauth_state = {
    "state": 'y90dsygas98dygoidsahf8sa',
    "access_token": None,
    "refresh_token": None,
}

def get_app_key_and_secret():
    app_key, app_secret = None, None
    with open(Path.home() / 'saxo-app-key.txt', 'r') as f:
        app_key = f.readline().strip()
    with open(Path.home() / 'saxo-app-secret.txt', 'r') as f:
        app_secret = f.readline().strip()
    return app_key, app_secret


def basic_auth_header(client_id: str, client_secret: str) -> str:
    token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


APP_KEY, APP_SECRET = get_app_key_and_secret()
AUTH_URL = 'https://sim.logonvalidation.net/authorize'
TOKEN_URL = 'https://sim.logonvalidation.net/token'
BASE_URL = 'https://gateway.saxobank.com/sim/openapi'
HOST = 'localhost'
PORT = 8000
REDIRECT_URI = f'http://{HOST}:{PORT}/callback'


@app.get('/')
def index():
    return '<a href="/login">Login with Saxo</a>'


@app.get('/exchanges')
def exchanges():
    url = f'{BASE_URL}/ref/v1/exchanges'
    t = oauth_state['access_token']
    params = {'$top': 500, '$skip': 0}
    headers = {'Authorization': f'Bearer {t}'}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()['Data']
    exchange_list = {}
    for item in data:
        exchange_list[item['Name']] = {
            'ExchangeId': item['ExchangeId'],
        }
    with open('exchanges.json', 'w') as f:
        json.dump(exchange_list, f, indent=4)
    return exchange_list


@app.get('/iwda.xams')
def iwda_xams():
    uic = 50629
    asset_type = 'Etf'
    session = requests.Session()
    t = oauth_state['access_token']
    session.headers.update({"Authorization": f"Bearer {t}"})


@app.get('/login')
def login():
    params = {
        'response_type': 'code',
        'client_id': APP_KEY,
        'redirect_uri': REDIRECT_URI,
        'state': 'y90dsygas98dygoidsahf8sa',
    }
    url = f'{AUTH_URL}?{urlencode(params)}'
    print(url)
    print(APP_KEY)
    print(REDIRECT_URI)
    response = redirect(url)
    return response


@app.get('/callback')
def oauth_callback():
    error = request.args.get("error")
    if error:
        return f"OAuth error: {error}", 400
    code = request.args.get("code")
    if not code:
        return 'Missing code', 400
    headers = {
        "Authorization": basic_auth_header(APP_KEY, APP_SECRET),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    if not r.ok:
        return f"Token exchange failed: {r.status_code}\n{r.text}", 500
    tok = r.json()
    oauth_state['access_token'] = tok["access_token"]
    oauth_state['refresh_token'] = tok.get("refresh_token")
    return redirect('/exchanges')


def main():
    app.run(HOST, PORT, debug=True)


if __name__ == '__main__':
    main()