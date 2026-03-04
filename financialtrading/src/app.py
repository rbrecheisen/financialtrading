from flask import Flask, redirect
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


APP_KEY, APP_SECRET = get_app_key_and_secret()
AUTH_URL = 'https://sim.logonvalidation.net/authorize'
TOKEN_URL = 'https://sim.logonvalidation.net/token'
HOST = 'localhost'
PORT = 8000
REDIRECT_URI = f'http://{HOST}:{PORT}/callback'


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
    print(url)
    print(APP_KEY)
    print(REDIRECT_URI)
    response = redirect(url)
    return response


@app.get('/callback')
def oauth_callback():
    print('OAuth 2.0 callback received')
    return "OK"


def main():
    app.run("localhost", 8000, debug=True)


if __name__ == '__main__':
    main()


# oauth_state = {
#     "state": None,
#     "code_verifier": None,
#     "access_token": None,
#     "refresh_token": None,
#     "error": None,
# }

# def basic_auth_header(client_id: str, client_secret: str) -> str:
#     token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
#     return f"Basic {token}"