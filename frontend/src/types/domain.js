/** @typedef {{username: string, display_name: string, role: 'owner'|'analyst'|'observer'}} User */
/** @typedef {{code: string, branch: 'north'|'south', worked_on: string, ribs: number, fabric: number, mechanism: number, minutes: number, note: string, revision: number}} Ticket */
/** @typedef {{id: number, plan_key: string, version: number, label: string, focus_branch: string, control_branch: string, coefficient_ref: 'focus'|'control', date_from: string, date_to: string, min_samples: number}} Plan */
/** @typedef {{id: number, status: 'queued'|'running'|'completed'|'failed', plan: Plan, sample_count: number, snapshot_sha: string}} Run */
export {};
