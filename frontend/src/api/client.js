import { state } from '../stores/workspace.js';

async function fetchResource(path, { method = 'GET', body, signal } = {}) {
  const headers = {};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, { method, headers, body: JSON.stringify(body), signal });
  if (response.ok) return response;
  const { detail } = await response.json().catch(() => ({}));
  const message = Array.isArray(detail)
    ? detail.map(entry => `${entry.loc.at(-1)} · ${entry.msg.replace('Value error, ', '')}`).join('；')
    : detail;
  if (response.status === 401 && state.token && path !== '/session') {
    window.dispatchEvent(new Event('session-expired'));
  }
  throw new Error(message || `请求失败（${response.status}），请重试。`);
}

export async function request(path, options) {
  return (await fetchResource(path, options)).json();
}

export async function download(path, filename) {
  const data = await (await fetchResource(path)).blob();
  const url = URL.createObjectURL(data);
  const link = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
