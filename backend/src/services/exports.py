import csv
from io import StringIO
from pathlib import Path

from src.config.settings import EXPORT_DIR


def snapshot_path(run_id, token):
    return EXPORT_DIR / f'run-{run_id}-{token}.json'


def write_snapshot(run_id, token, data):
    path = snapshot_path(run_id, token)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(f'{path}.tmp')
    temporary.write_text(data, encoding='utf-8')
    temporary.replace(path)


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
