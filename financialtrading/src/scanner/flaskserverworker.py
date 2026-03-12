import base64
import json
import requests
from flask import Flask
from flask import Flask, redirect, request
from urllib.parse import urlencode
from pathlib import Path
from werkzeug.serving import make_server
from PySide6.QtCore import QObject, Signal, Slot


def create_flask_app(app_key, app_secret, redirect_uri, auth_url, token_url, tokeninfo_file):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return '<a href="/login">Login with Saxo</a>'
    
    @app.get('/login')
    def login():
        params = {
            'response_type': 'code',
            'client_id': app_key,
            'redirect_uri': redirect_uri,
            'state': 'y90dsygas98dygoidsahf8sa',
        }
        url = f'{auth_url}?{urlencode(params)}'
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
            "Authorization": basic_auth_header(app_key, app_secret),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        r = requests.post(token_url, headers=headers, data=data, timeout=30)
        if not r.ok:
            return f"Token exchange failed: {r.status_code}\n{r.text}", 500
        tok = r.json()
        print(f'Writing token info: {tok}')
        with open(tokeninfo_file, 'w') as f:
            json.dump(tok, f, indent=4)
        return "OK"

    return app


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


class FlaskServerWorker(QObject):
    started = Signal(str)       # emits server URL
    stopped = Signal()
    failed = Signal(str)

    def __init__(self, tokeninfo_file, host="localhost", port=8000, parent=None):
        super().__init__(parent)
        self.tokeninfo_file = tokeninfo_file
        self.host = host
        self.port = port
        self.auth_url = 'https://sim.logonvalidation.net/authorize'
        self.token_url = 'https://sim.logonvalidation.net/token'
        self.base_url = 'https://gateway.saxobank.com/sim/openapi'
        self.redirect_uri = f'http://{self.host}:{self.port}/callback'
        self.app_key, self.app_secret = get_app_key_and_secret()
        self._server = None
        self._running = False

    @Slot()
    def start_server(self):
        if self._running:
            return
        try:
            app = create_flask_app(self.app_key, self.app_secret, self.redirect_uri, self.auth_url, self.token_url, self.tokeninfo_file)
            self._server = make_server(self.host, self.port, app)
            self._running = True
            self.started.emit(f"http://{self.host}:{self.port}")
            self._server.serve_forever()
        except OSError as e:
            self.failed.emit(f"Could not start server: {e}")
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            self._running = False
            self._server = None
            self.stopped.emit()

    @Slot()
    def stop_server(self):
        if self._server is not None:
            self._server.shutdown()