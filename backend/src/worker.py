import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from redis.exceptions import RedisError

from src.models.db import transaction
from src.services.audit import record
from src.services.decomposition import AnalysisError, analyze
from src.services.exports import write_snapshot
from src.utils.queue import WAKE_KEY, redis
from src.utils.serialization import canonical, checksum

logger = logging.getLogger(__name__)
heartbeat = Path('/tmp/umbrella-worker')


def claim():
    with transaction() as cursor:
        cursor.execute("SELECT id, snapshot, snapshot_sha FROM analysis_runs WHERE status='queued' "
                       "OR (status='running' AND claimed_at < UTC_TIMESTAMP(6) - INTERVAL 30 SECOND) "
                       'ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED')
        job = cursor.fetchone()
        if job:
            job['token'] = uuid4().hex
            cursor.execute("UPDATE analysis_runs SET status='running', claim_token=%s, claimed_at=UTC_TIMESTAMP(6) "
                           'WHERE id=%s', (job['token'], job['id']))
    return job


def process(job):
    run_id, token = job['id'], job['token']
    failure = result = None
    try:
        snapshot = json.loads(job['snapshot'])
        text = canonical(snapshot)
        if checksum(text) != job['snapshot_sha']:
            raise AnalysisError('输入快照校验失败，请重新提交运行。')
        calculated = canonical(analyze(snapshot))
        write_snapshot(run_id, token, text)
        result = calculated
    except AnalysisError as exc:
        failure = str(exc)
    except Exception:
        logger.exception('Analysis or export failed for run %s', run_id)
        failure = '计算或快照保存中断，请重新提交运行。'
    status = 'failed' if failure else 'completed'
    with transaction() as cursor:
        cursor.execute('UPDATE analysis_runs SET status=%s, result=%s, failure=%s, finished_at=UTC_TIMESTAMP(6) '
                       "WHERE id=%s AND claim_token=%s AND status='running'", (status, result, failure, run_id, token))
        if cursor.rowcount:
            record(cursor, 'worker', f'run.{status}', run_id)


def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            job = claim()
            heartbeat.touch()
            if job:
                process(job)
                continue
        except Exception:
            logger.exception('Worker could not process queue')
            time.sleep(2)
            continue
        try:
            redis.blpop(WAKE_KEY, timeout=2)
        except RedisError:
            time.sleep(2)


if __name__ == '__main__':
    main()
