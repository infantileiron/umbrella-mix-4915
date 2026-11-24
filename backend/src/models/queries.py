TICKET_COLUMNS = 'code, branch, worked_on, ribs, fabric, mechanism, minutes, note, revision'
PLAN_COLUMNS = ('id, plan_key, version, label, focus_branch, control_branch, coefficient_ref, '
                'date_from, date_to, min_samples, created_by')
RUN_COLUMNS = ('id, plan_id, status, snapshot_sha, failure, created_by, created_at, finished_at')
DRAFT_COLUMNS = 'run_id, action_text, status, edited_by, edited_at'
