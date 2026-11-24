import { ROLE } from '../constants/domain.js';
import { links } from '../router/routes.js';
import { esc } from '../utils/html.js';

export const brand = `<div class="brand-mark" aria-hidden="true"><span></span></div>
  <div class="brand-name">补雨修伞<small>跨网点工时拆解</small></div>`;

export function shell(active, user) {
  return `<aside class="sidebar">
    <div class="brand">${brand}</div>
    <nav aria-label="工作区">${links.map(([name, mark, label]) =>
      `<a href="#/${name}"${active === name ? ' aria-current="page"' : ''}><i>${mark}</i>${label}</a>`).join('')}</nav>
    <div class="sidebar-bottom"><div class="user"><b>${esc(user.display_name.split(' ')[0])}</b>
      <span>${esc(ROLE[user.role])}</span></div><button type="button" data-logout>退出登录 ↗</button></div>
  </aside>
  <div class="desk"><div class="topbar"><span>返修计时工作台</span><span class="top-unit">工时单位 / 分钟每票</span></div>
    <main id="view" class="view" aria-live="polite"></main></div><div id="overlay"></div>`;
}
