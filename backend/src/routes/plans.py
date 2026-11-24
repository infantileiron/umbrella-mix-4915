from fastapi import APIRouter, Depends

from src.controllers.access import analyst, current_user
from src.schemas.inputs import NewPlan, PlanKey, PlanRevision
from src.services import plans

router = APIRouter(prefix='/plans')


@router.get('')
def index(user=Depends(current_user)):
    return plans.list_plans()


@router.post('', status_code=201)
def create(payload: NewPlan, user=Depends(analyst)):
    return plans.save_plan(payload.plan_key, payload, user['username'])


@router.post('/{key}/versions', status_code=201)
def revise(key: PlanKey, payload: PlanRevision, user=Depends(analyst)):
    return plans.save_plan(key, payload, user['username'], base=payload.base_version)
