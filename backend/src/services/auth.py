from fastapi import HTTPException

from src.models.db import transaction
from src.utils.security import issue_token, verify_password

DUMMY_PASSWORD_HASH = '0' * 32 + '$' + '0' * 64


def login(payload):
    with transaction() as cursor:
        cursor.execute('SELECT username, display_name, role, password_hash FROM users WHERE username=%s',
                       (payload.username,))
        user = cursor.fetchone()
    stored = user.pop('password_hash') if user else DUMMY_PASSWORD_HASH
    if not verify_password(payload.password, stored) or not user:
        raise HTTPException(401, '账号或口令不正确')
    return {'token': issue_token(user['username']), 'user': user}
