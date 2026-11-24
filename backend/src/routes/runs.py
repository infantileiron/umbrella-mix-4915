from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from src.constants.domain import RunStatus
from src.controllers.access import analyst, current_user, owner
from src.schemas.inputs import DraftText, StartRun
from src.services import runs
from src.services.exports import csv_result, ensure_artifact

router = APIRouter(prefix='/runs')


@router.get('')
def index(user=Depends(current_user)):
    return runs.list_runs(user['role'])


@router.post('', status_code=202)
def submit(payload: StartRun, user=Depends(analyst)):
    return runs.submit(payload.plan_id, user['username'])


@router.get('/{run_id}')
def detail(run_id: int, user=Depends(current_user)):
    run = runs.get_run(run_id, user['role'])
    del run['claim_token']
    return run


@router.put('/{run_id}/draft')
def draft(run_id: int, payload: DraftText, user=Depends(owner)):
    return runs.put_draft(run_id, user['username'], action_text=payload.action_text)


@router.post('/{run_id}/publish')
def publish(run_id: int, user=Depends(owner)):
    return runs.put_draft(run_id, user['username'], publish=True)


def completed(run_id, user):
    run = runs.get_run(run_id, user['role'])
    if run['status'] != RunStatus.COMPLETED:
        raise HTTPException(409, '运行完成后可导出')
    return run


@router.get('/{run_id}/result.csv')
def export_csv(run_id: int, user=Depends(current_user)):
    return Response(csv_result(completed(run_id, user)), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="umbrella-{run_id}.csv"'})


@router.get('/{run_id}/snapshot.json')
def export_snapshot(run_id: int, user=Depends(current_user)):
    completed(run_id, user)
    data = ensure_artifact(run_id)
    return Response(data, media_type='application/json',
                    headers={'Content-Disposition': f'attachment; filename="umbrella-{run_id}-snapshot.json"'})
