from fastapi import APIRouter, Depends, Query

from src.constants.domain import Branch
from src.controllers.access import analyst, current_user
from src.schemas.inputs import NewTicket, TicketCode, TicketEdit
from src.services import tickets

router = APIRouter(prefix='/tickets')


@router.get('')
def index(branch: Branch | None = None, page: int = Query(1, ge=1, le=100_000),
          size: int = Query(8, ge=1, le=100), user=Depends(current_user)):
    return tickets.list_tickets(branch, page, size)


@router.post('', status_code=201)
def create(payload: NewTicket, user=Depends(analyst)):
    return tickets.create_ticket(payload, user['username'])


@router.put('/{code}')
def edit(code: TicketCode, payload: TicketEdit, user=Depends(analyst)):
    return tickets.edit_ticket(code, payload, user['username'])
