import { esc } from '../../utils/html.js';

export function heading(section, title, description, actions = '') {
  return `<header class="page-heading">
    <div><div class="kicker"><span></span>${esc(section)}</div><h1>${esc(title)}</h1><p>${esc(description)}</p></div>
    <div class="heading-actions">${actions}</div>
  </header>`;
}
