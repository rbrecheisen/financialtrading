import json
import time
import requests
from pathlib import Path


class TokenManager:
    """
    Allows retrieval (through OAuth 2.0) of access and refresh tokens. The 
    refresh token is storedd locally so it can be used to get a new access
    token whenever necessary.
    """
    def __init__(self, tokens_file='tokens.json', base_url='https://gateway.saxobank.com/sim/openapi', token_url='https://sim.logonvalidation.net/token'):
        self._tokens_file = Path(tokens_file)
        self._tokens = self.load_tokens(self._tokens_file)
        self._base_url = base_url
        self._token_url = token_url
        self._access_token = self.refresh_if_needed(self._tokens)

    def load_tokens(self, tokens_file):
        return json.loads(tokens_file.read_text())
    
    def save_tokens(self, tokens_file, tokens):
        tokens_file.write_text(tokens)

    def refresh_if_needed(self, tokens):
        if time.time() < tokens['expires_at'] - 30:
            return tokens['access_token']
        result = requests.post(
            self._token_url,
            auth=(self.load_app_key(), self.load_app_secret()),
            data={'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30,
        )
        result.raise_for_status()
        new_tokens = result.json()
        new_tokens['expires_at'] = time.time() + int(new_tokens['expires_in'])
        self.save_tokens(new_tokens)
        return new_tokens['access_token']

    def load_app_key(self):
        with open(Path.home() / 'saxo-app-key.txt', 'r') as f:
            app_key = f.readline().strip()
            return app_key
        
    def load_app_secret(self):
        with open(Path.home() / 'saxo-app-secret.txt', 'r') as f:
            app_secret = f.readline().strip()
            return app_secret