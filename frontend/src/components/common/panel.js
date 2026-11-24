import { esc } from '../../utils/html.js';

export function panel(title, caption, content, extra = '') {
  return `<section class="panel ${esc(extra)}"><header class="panel-head"><h2>${esc(title)}</h2>
    ${caption ? `<span>${esc(caption)}</span>` : ''}</header>${content}</section>`;
}

export function empty(title, text, action = '') {
  return `<section class="empty-panel"><h2>${esc(title)}</h2><p>${esc(text)}</p>${action}</section>`;
}
