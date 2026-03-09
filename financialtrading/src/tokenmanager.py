import base64
import json
import requests
import time
from flask import Flask, redirect, request
from urllib.parse import urlencode
from pathlib import Path

app = Flask(__name__)


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
TIMEOUT = 60*15


@app.get('/')
def index():
    return '<a href="/login">Login with Saxo</a>'


@app.get('/login')
def login():
    params = {
        'response_type': 'code',
        'client_id': APP_KEY,
        'redirect_uri': REDIRECT_URI,
        'state': 'y90dsygas98dygoidsahf8sa',
    }
    url = f'{AUTH_URL}?{urlencode(params)}'
    response = redirect(url)
    return response


def refresh_token(app_key: str, app_secret: str, current_refresh_token: str) -> dict:
    headers = {
        "Authorization": basic_auth_header(app_key, app_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": current_refresh_token,
    }
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()


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
    while True:
        print(f'Writing token info: {tok}')
        with open('tokeninfo.json', 'w') as f:
            json.dump(tok, f, indent=4)
        time.sleep(TIMEOUT)
        print(f'Refreshing token...')
        tok = refresh_token(APP_KEY, APP_SECRET, tok['refresh_token'])


def main():
    app.run(HOST, PORT, debug=True)


if __name__ == '__main__':
    main()