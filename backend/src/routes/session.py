from fastapi import APIRouter, Depends

from src.controllers.access import current_user
from src.schemas.inputs import Login
from src.services.auth import login

router = APIRouter()


@router.post('/session')
def create_session(payload: Login):
    return login(payload)


@router.get('/session')
def session(user=Depends(current_user)):
    return user
