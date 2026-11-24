import { download, request } from './client.js';

export const api = {
  login: body => request('/session', { method: 'POST', body }),
  session: () => request('/session'),
  tickets: (branch, page) => request(`/tickets?page=${page}${branch ? `&branch=${branch}` : ''}`),
  saveTicket: (body, code) => request(code ? `/tickets/${encodeURIComponent(code)}` : '/tickets',
    { method: code ? 'PUT' : 'POST', body }),
  plans: () => request('/plans'),
  savePlan: (body, key) => request(key ? `/plans/${encodeURIComponent(key)}/versions` : '/plans',
    { method: 'POST', body }),
  runs: () => request('/runs'),
  run: id => request(`/runs/${id}`),
  submitRun: planId => request('/runs', { method: 'POST', body: { plan_id: planId } }),
  saveDraft: (id, text) => request(`/runs/${id}/draft`, { method: 'PUT', body: { action_text: text } }),
  publish: id => request(`/runs/${id}/publish`, { method: 'POST' }),
  exportResult: id => download(`/runs/${id}/result.csv`, `umbrella-${id}.csv`),
  exportSnapshot: id => download(`/runs/${id}/snapshot.json`, `umbrella-${id}-snapshot.json`),
};
