export const esc = value => String(value ?? '').replace(/[&<>"']/g, char =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

export function options(labels, selected) {
  return Object.entries(labels).map(([key, label]) =>
    `<option value="${esc(key)}"${key === String(selected) ? ' selected' : ''}>${esc(label)}</option>`).join('');
}
