import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.constants.domain import Role
from src.models.db import transaction
from src.utils.security import token_subject

bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        username = token_subject(credentials.credentials) if credentials else None
    except jwt.InvalidTokenError:
        username = None
    if username:
        with transaction() as cursor:
            cursor.execute('SELECT username, display_name, role FROM users WHERE username=%s', (username,))
            user = cursor.fetchone()
        if user:
            return user
    raise HTTPException(401, '请重新登录', headers={'WWW-Authenticate': 'Bearer'})


def analyst(user=Depends(current_user)):
    if user['role'] != Role.ANALYST:
        raise HTTPException(403, '样本、方案和运行由分析员维护')
    return user


def owner(user=Depends(current_user)):
    if user['role'] != Role.OWNER:
        raise HTTPException(403, '改进草案和发布由业务方负责')
    return user
