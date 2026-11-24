import { api } from '../api/workspace.js';
import { heading } from '../components/common/heading.js';
import { table } from '../components/common/table.js';
import { dialog, field, select } from '../components/common/form.js';
import { BRANCH, DATE_TO } from '../constants/domain.js';
import { openSheet } from '../hooks/forms.js';
import { state } from '../stores/workspace.js';
import { number } from '../utils/format.js';
import { esc, options } from '../utils/html.js';

function summary(branches) {
  return `<section class="ledger-summary" aria-label="网点工票汇总">${Object.entries(BRANCH).map(([key, label]) => {
    const branch = branches.find(item => item.branch === key);
    return `<article class="branch-summary ${key}"><div><span class="branch-code">${key === 'north' ? 'BE' : 'NQ'}</span><h2>${label}</h2></div>
      <div class="branch-values"><span><strong>${branch?.tickets ?? 0}</strong> 张工票</span>
      <span><strong>${number(branch?.mean_minutes)}</strong> 分钟/票</span></div></article>`;
  }).join('')}</section>`;
}

function editor(ticket) {
  const fields = ticket || { worked_on: DATE_TO, branch: 'south', ribs: 1, fabric: 0, minutes: '', mechanism: 0 };
  return dialog(ticket ? `修订工票 ${ticket.code}` : '录入工票', `<div class="form-grid">
    ${ticket ? '' : field('工票编号', 'code', '', 'required pattern="[A-Z0-9][A-Z0-9\\-]{2,31}" placeholder="如 NQ-W46-33"')}
    ${select('网点', 'branch', options(BRANCH, fields.branch))}
    ${field('返修日期', 'worked_on', fields.worked_on, 'type="date" required')}
    ${field('伞骨更换（根）', 'ribs', fields.ribs, 'type="number" min="0" max="12" required')}
    ${field('布面损伤（处）', 'fabric', fields.fabric, 'type="number" min="0" max="12" required')}
    ${select('开合机构', 'mechanism', options({ 0: '无需修', 1: '需要修' }, fields.mechanism))}
    ${field('返修工时（分钟）', 'minutes', fields.minutes, 'type="number" min="1" max="480" required')}
    <label class="full">备注<textarea name="note" rows="2" maxlength="180">${esc(fields.note)}</textarea></label></div>`,
    ticket ? '保存修订' : '保存工票');
}

export async function tickets({ view, refresh, active }) {
  const { branch, page } = state.ledger;
  const data = await api.tickets(branch, page);
  if (!active()) return;
  const write = state.user.role === 'analyst';
  const rows = data.items.map(item => [
    `<b class="mono">${esc(item.code)}</b>`, `<span class="branch-label ${esc(item.branch)}">${BRANCH[item.branch]}</span>`,
    `<span class="mono">${esc(item.worked_on)}</span>`, item.ribs, item.fabric, item.mechanism ? '需修' : '—',
    `<b class="mono minutes">${item.minutes}</b>`, esc(item.note),
    ...(write ? [`<button class="text-btn" type="button" data-edit="${esc(item.code)}">修订</button>`] : []),
  ]);
  const maxPage = Math.max(1, Math.ceil(data.total / data.size));
  view.innerHTML = heading('工票台账', '网点任务账', '登记返修工序和有效作业分钟，为跨网点比较保留逐票依据。',
    write ? '<button class="btn primary" type="button" data-new>＋ 录入工票</button>' : '') + summary(data.branches) + `
    <section class="panel"><header class="panel-head ledger-tools"><h2>返修明细 <small id="ticket-total">${data.total} 张</small></h2>
    <div class="filters" aria-label="筛选网点">${Object.entries({ '': '全部', ...BRANCH }).map(([key, label]) =>
      `<button type="button" data-branch="${key}" aria-pressed="${key === branch}">${label}</button>`).join('')}</div></header>
    ${table(['工票编号', '网点', '返修日期', '换骨 / 根', '布损 / 处', '开合机构', '工时 / 分', '备注', ...(write ? ['操作'] : [])], rows,
    '所选网点暂无工票。分析员可登记返修记录。')}
    <div class="pagination"><span>第 ${page} / ${maxPage} 页</span><button class="btn" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>上一页</button>
    <button class="btn" data-page="${page + 1}" ${page >= maxPage ? 'disabled' : ''}>下一页</button></div></section>`;
  view.querySelectorAll('[data-branch]').forEach(button => button.onclick = () => {
    state.ledger = { branch: button.dataset.branch, page: 1 };
    refresh();
  });
  view.querySelectorAll('[data-page]').forEach(button => button.onclick = () => {
    state.ledger.page = Number(button.dataset.page);
    refresh();
  });
  const open = ticket => openSheet(document.querySelector('#overlay'), editor(ticket), async fields => {
    for (const key of ['ribs', 'fabric', 'minutes', 'mechanism']) fields[key] = Number(fields[key]);
    if (ticket) fields.revision = ticket.revision;
    await api.saveTicket(fields, ticket?.code);
    if (!ticket) state.ledger = { branch: '', page: 1 };
    refresh();
  });
  if (write) {
    view.querySelector('[data-new]').onclick = () => open();
    view.querySelectorAll('[data-edit]').forEach(button => button.onclick = () =>
      open(data.items.find(item => item.code === button.dataset.edit)));
  }
}
