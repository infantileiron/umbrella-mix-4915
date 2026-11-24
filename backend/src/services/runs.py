import json

from fastapi import HTTPException

from src.constants.domain import DraftStatus, METHOD, Role, RunStatus
from src.models.db import transaction
from src.models.queries import DRAFT_COLUMNS, PLAN_COLUMNS, RUN_COLUMNS, TICKET_COLUMNS
from src.services.audit import record
from src.utils.queue import wake_worker
from src.utils.serialization import canonical, checksum


def submit(plan_id, actor):
    with transaction() as cursor:
        cursor.execute(f'SELECT {PLAN_COLUMNS} FROM comparison_plans WHERE id=%s', (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            raise HTTPException(404, '未找到方案版本')
        cursor.execute(f'SELECT {TICKET_COLUMNS} FROM tickets WHERE branch IN (%s,%s) '
                       'AND worked_on BETWEEN %s AND %s ORDER BY code',
                       (plan['focus_branch'], plan['control_branch'], plan['date_from'], plan['date_to']))
        tickets = cursor.fetchall()
        snapshot = canonical(dict(method=METHOD, plan=plan, tickets=tickets))
        digest = checksum(snapshot)
        cursor.execute('INSERT INTO analysis_runs (plan_id, snapshot, snapshot_sha, created_by) VALUES (%s,%s,%s,%s)',
                       (plan_id, snapshot, digest, actor))
        run_id = cursor.lastrowid
        record(cursor, actor, 'run.submit', run_id)
    wake_worker()
    return dict(id=run_id, status=RunStatus.QUEUED, snapshot_sha=digest)


def list_runs(role):
    clause = "WHERE d.status='published'" if role == Role.OBSERVER else ''
    columns = ', '.join(f'r.{column}' for column in RUN_COLUMNS.split(', '))
    with transaction() as cursor:
        cursor.execute(f'SELECT {columns}, p.plan_key, p.version, p.label, d.status AS review_status '
                       'FROM analysis_runs r JOIN comparison_plans p ON p.id=r.plan_id '
                       f'LEFT JOIN improvement_drafts d ON d.run_id=r.id {clause} ORDER BY r.id DESC')
        return cursor.fetchall()


def get_run(run_id, role):
    with transaction() as cursor:
        cursor.execute(f'SELECT {RUN_COLUMNS}, snapshot, result, claim_token FROM analysis_runs WHERE id=%s', (run_id,))
        run = cursor.fetchone()
        if not run:
            raise HTTPException(404, '未找到可阅运行')
        cursor.execute(f'SELECT {DRAFT_COLUMNS} FROM improvement_drafts WHERE run_id=%s', (run_id,))
        draft = cursor.fetchone()
    if role == Role.OBSERVER and (not draft or draft['status'] != DraftStatus.PUBLISHED):
        raise HTTPException(404, '未找到可阅运行')
    snapshot = json.loads(run.pop('snapshot'))
    run['result'] = json.loads(run['result']) if run['result'] is not None else None
    run['plan'] = snapshot['plan']
    run['sample_count'] = len(snapshot['tickets'])
    run['draft'] = draft
    return run


def put_draft(run_id, actor, action_text=None, publish=False):
    with transaction() as cursor:
        cursor.execute('SELECT status FROM analysis_runs WHERE id=%s FOR UPDATE', (run_id,))
        run = cursor.fetchone()
        if not run:
            raise HTTPException(404, '运行不存在')
        if run['status'] != RunStatus.COMPLETED:
            raise HTTPException(409, '仅已完成的运行可进入复核')
        cursor.execute('SELECT status FROM improvement_drafts WHERE run_id=%s', (run_id,))
        draft = cursor.fetchone()
        if draft and draft['status'] == DraftStatus.PUBLISHED:
            raise HTTPException(409, '此草案已发布，若需变更请重新运行并复核')
        if publish:
            if not draft:
                raise HTTPException(409, '请先保存改进草案')
            cursor.execute("UPDATE improvement_drafts SET status='published', edited_by=%s, edited_at=UTC_TIMESTAMP(6) "
                           'WHERE run_id=%s', (actor, run_id))
        else:
            cursor.execute("INSERT INTO improvement_drafts (run_id, action_text, status, edited_by) VALUES (%s,%s,'draft',%s) "
                           'ON DUPLICATE KEY UPDATE action_text=%s, edited_by=%s, edited_at=UTC_TIMESTAMP(6)',
                           (run_id, action_text, actor, action_text, actor))
        record(cursor, actor, 'draft.publish' if publish else 'draft.save', run_id)
        cursor.execute(f'SELECT {DRAFT_COLUMNS} FROM improvement_drafts WHERE run_id=%s', (run_id,))
        return cursor.fetchone()
