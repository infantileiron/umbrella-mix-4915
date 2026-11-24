import csv
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from io import StringIO
from uuid import uuid4

from fastapi import HTTPException

from src.config.settings import EXPORT_DIR
from src.models.db import transaction
from src.services.audit import record
from src.utils.serialization import canonical, checksum

logger = logging.getLogger(__name__)

AVAILABLE = 'available'
PENDING = 'pending'
UNRECOVERABLE = 'unrecoverable'

UNAVAILABLE_MESSAGE = '原件指纹与封存内容不符，无法恢复；周报结论和其他完好原件仍可照常取用。'
RETRY_MESSAGE = '原件暂不可用，请稍后重试。'


def snapshot_path(run_id):
    return EXPORT_DIR / f'run-{run_id}.json'


def legacy_snapshot_path(run_id, token):
    return EXPORT_DIR / f'run-{run_id}-{token}.json'


def artifact_files(run_id, token=None):
    """Every file that could hold this run's sealed original.

    New writes use the stable ``run-<id>.json`` name. Earlier workers named the
    file after the claim token, so a job that was reclaimed left its first file
    under a token the current row no longer carries. Validate all candidates
    before concluding an original is gone.
    """
    paths = [snapshot_path(run_id)]
    if token:
        legacy = legacy_snapshot_path(run_id, token)
        if legacy not in paths:
            paths.append(legacy)
    try:
        for path in sorted(EXPORT_DIR.glob(f'run-{run_id}-*.json')):
            if path not in paths:
                paths.append(path)
    except OSError:
        logger.warning('Could not scan export directory %s', EXPORT_DIR)
    return paths


def read_verified(path, digest):
    """Bytes of the file only when its SHA-256 matches the published fingerprint."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(data).hexdigest() != digest:
        return None
    return data


def locate_artifact(run_id, token, digest):
    for path in artifact_files(run_id, token):
        data = read_verified(path, digest)
        if data is not None:
            return path, data
    return None


def _iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds') if value else None


def _mtime(path):
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def write_atomic(path, text):
    """Replace the served file in one step so an interrupted repair never
    leaves a half-written snapshot under the downloadable name."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid4().hex}.tmp')
    try:
        with open(temporary, 'wb') as handle:
            handle.write(text.encode('utf-8'))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def write_snapshot(run_id, text, digest):
    """Worker entry point: materialise the freshly-computed snapshot once.

    Writing under the stable name means a later pickup can always find the
    original, even if the job is retried and its claim token changes.
    """
    if checksum(text) != digest:
        raise ValueError('快照内容与提交时指纹不一致')
    path = snapshot_path(run_id)
    if read_verified(path, digest) is not None:
        return path
    write_atomic(path, text)
    if read_verified(path, digest) is None:
        raise OSError('快照写入后未通过指纹核对')
    return path


def sealed_matches(snapshot_raw, digest):
    """Canonical bytes of the sealed input, or None when they do not match.

    The sealed snapshot is the source of truth for a rebuild: only content
    whose fingerprint equals the one recorded at submission may be handed out.
    """
    try:
        text = canonical(json.loads(snapshot_raw))
    except (TypeError, ValueError):
        return None
    return text if checksum(text) == digest else None


def _record_once(cursor, action, run_id):
    cursor.execute('SELECT 1 FROM audit_events WHERE action=%s AND subject=%s LIMIT 1',
                   (action, str(run_id)))
    if not cursor.fetchone():
        record(cursor, 'system', action, run_id)


def inspect_artifact(run_id, token, digest, snapshot_raw):
    """Read-only view of whether the original can be handed out right now.

    Nothing is repaired here. A missing but sealed-intact original stays
    ``pending`` until someone picks it up; an original whose sealed content no
    longer matches its fingerprint is reported as ``unrecoverable``.
    """
    found = locate_artifact(run_id, token, digest)
    if found:
        path, _ = found
        return dict(state=AVAILABLE, available_at=_iso(_mtime(path)), expected_sha256=digest)
    if sealed_matches(snapshot_raw, digest) is None:
        return dict(state=UNRECOVERABLE, available_at=None, expected_sha256=digest,
                    message=UNAVAILABLE_MESSAGE)
    return dict(state=PENDING, available_at=None, expected_sha256=digest)


def reconcile(run_id):
    """Return ``(state, bytes)`` for a run's original, rebuilding if needed.

    The row lock serialises concurrent pickups and retries after an
    interruption. A verified file is reused exactly as it is, so the same
    original is materialised at most once; a file that fails the fingerprint
    check is never handed out and is replaced only from sealed content that
    matches the published fingerprint.
    """
    with transaction() as cursor:
        cursor.execute('SELECT snapshot, snapshot_sha, claim_token FROM analysis_runs WHERE id=%s FOR UPDATE',
                       (run_id,))
        row = cursor.fetchone()
        if not row:
            return None, None
        digest = row['snapshot_sha']
        found = locate_artifact(run_id, row['claim_token'], digest)
        if found:
            return AVAILABLE, found[1]
        text = sealed_matches(row['snapshot'], digest)
        if text is None:
            _record_once(cursor, 'artifact.unrecoverable', run_id)
            return UNRECOVERABLE, None
        path = snapshot_path(run_id)
        try:
            write_atomic(path, text)
        except OSError:
            logger.exception('Could not rebuild snapshot for run %s', run_id)
            return PENDING, None
        if read_verified(path, digest) is None:
            logger.error('Rebuilt snapshot for run %s failed verification', run_id)
            return PENDING, None
        _record_once(cursor, 'artifact.recover', run_id)
        return AVAILABLE, text.encode('utf-8')


def ensure_artifact(run_id):
    """Verified snapshot bytes for download, repairing a lost original first."""
    state, data = reconcile(run_id)
    if state is None:
        raise HTTPException(404, '未找到可阅运行')
    if state == UNRECOVERABLE:
        raise HTTPException(410, UNAVAILABLE_MESSAGE)
    if data is None:
        raise HTTPException(503, RETRY_MESSAGE)
    return data


def _safe(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + value
    return value


def csv_result(run):
    output = StringIO(newline='')
    writer = csv.writer(output)
    result, plan = run['result'], run['plan']
    rows = [('section', 'key', 'focus', 'control', 'composition_minutes', 'coefficient_minutes', 'value')]
    for key in ('method', 'gap', 'remainder', 'counterfactual'):
        rows.append(('summary', key, '', '', '', '', result[key]))
    rows.append(('summary', 'totals', '', '', result['composition'], result['coefficient'], ''))
    for key in ('branch', 'n', 'mean_minutes', 'rank', 'condition', 'r_squared', 'rmse'):
        rows.append(('fit', key, result['focus'][key], result['control'][key], '', '', ''))
    for term in result['terms']:
        key = term['term']
        rows.append(('contribution', key, '', '', term['composition'], term['coefficient'], ''))
        for metric in ('mean', 'coefficient'):
            rows.append((metric, key, result['focus']['terms'][key][metric],
                         result['control']['terms'][key][metric], '', '', ''))
    support = result['extrapolation']
    for key in ('evaluated_branch', 'basis_branch', 'outside', 'total', 'share'):
        rows.append(('support', key, '', '', '', '', support[key]))
    for term, values in support['terms'].items():
        for key, value in values.items():
            rows.append(('support', f'{term}.{key}', '', '', '', '', value))
    for key in ('plan_key', 'version', 'label', 'focus_branch', 'control_branch', 'date_from', 'date_to',
                'min_samples', 'coefficient_ref'):
        rows.append(('plan', key, '', '', '', '', plan[key]))
    rows.append(('run', 'snapshot_sha256', '', '', '', '', run['snapshot_sha']))
    if run['draft']:
        for key in ('status', 'action_text', 'edited_by'):
            rows.append(('review', key, '', '', '', '', run['draft'][key]))
    writer.writerows([_safe(value) for value in row] for row in rows)
    return '\ufeff' + output.getvalue()
