import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from src.config.settings import JWT_SECRET


def hash_password(password):
    salt = secrets.token_hex(16)
    return f'{salt}${_derive(password, salt)}'


def _derive(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 240_000).hex()


def verify_password(password, stored):
    salt, digest = stored.split('$', 1)
    return hmac.compare_digest(_derive(password, salt), digest)


def issue_token(username):
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({'sub': username, 'exp': expires, 'aud': 'umbrella-mix'}, JWT_SECRET, algorithm='HS256')


def token_subject(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'], audience='umbrella-mix',
                      options={'require': ['sub', 'exp', 'aud']})['sub']
