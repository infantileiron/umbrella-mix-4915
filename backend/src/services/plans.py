from fastapi import HTTPException
from pymysql.err import IntegrityError

from src.models.db import transaction
from src.models.queries import PLAN_COLUMNS
from src.services.audit import record


def list_plans():
    with transaction() as cursor:
        cursor.execute(f'SELECT {PLAN_COLUMNS} FROM comparison_plans ORDER BY plan_key, version DESC')
        return cursor.fetchall()


def save_plan(key, payload, actor, base=None):
    fields = payload.model_dump(exclude={'plan_key', 'base_version'})
    try:
        with transaction() as cursor:
            if base is not None:
                cursor.execute('SELECT MAX(version) AS version FROM comparison_plans WHERE plan_key=%s', (key,))
                latest = cursor.fetchone()['version']
                if latest is None:
                    raise HTTPException(404, '比较方案不存在')
                if latest != base:
                    raise HTTPException(409, '已有更新版本，请从最新方案另存')
            version = 1 if base is None else base + 1
            cursor.execute(f'INSERT INTO comparison_plans ({PLAN_COLUMNS.removeprefix("id, ")}) '
                           'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (key, version, *fields.values(), actor))
            plan_id = cursor.lastrowid
            record(cursor, actor, 'plan.create' if base is None else 'plan.revise', f'{key}.v{version}')
    except IntegrityError as exc:
        if exc.args[0] != 1062:
            raise
        raise HTTPException(409, '方案编号或版本已存在，请刷新后重试') from exc
    return dict(id=plan_id, plan_key=key, version=version, **fields, created_by=actor)
