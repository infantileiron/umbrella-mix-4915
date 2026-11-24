import { api } from '../api/workspace.js';
import { dialog, field, select } from '../components/common/form.js';
import { heading } from '../components/common/heading.js';
import { panel } from '../components/common/panel.js';
import { table } from '../components/common/table.js';
import { BASIS, BRANCH, DATE_FROM, DATE_TO } from '../constants/domain.js';
import { openSheet } from '../hooks/forms.js';
import { go } from '../router/routes.js';
import { state } from '../stores/workspace.js';
import { esc, options } from '../utils/html.js';

function editor(plan) {
  const values = plan || { focus_branch: 'south', control_branch: 'north', coefficient_ref: 'control',
    date_from: DATE_FROM, date_to: DATE_TO, min_samples: 12 };
  return dialog(plan ? `另存 ${plan.plan_key} 的新版本` : '新建比较方案', `<div class="form-grid">
    ${plan ? '' : field('方案编号', 'plan_key', '', 'required pattern="[A-Z0-9][A-Z0-9\\-]{2,31}" placeholder="如 RAIN-W46"')}
    ${field('方案名称', 'label', values.label, 'required maxlength="100"')}
    ${select('比较网点（A）', 'focus_branch', options(BRANCH, values.focus_branch))}
    ${select('对照网点（B）', 'control_branch', options(BRANCH, values.control_branch))}
    ${select('构成差使用的系数', 'coefficient_ref', options(BASIS, values.coefficient_ref))}
    ${field('每网点最低票数', 'min_samples', values.min_samples, 'type="number" min="8" max="500" required')}
    ${field('起始日期（含）', 'date_from', values.date_from, 'type="date" required')}
    ${field('结束日期（含）', 'date_to', values.date_to, 'type="date" required')}
    <p class="field-note full">差额采用「比较网点 A − 对照网点 B」。另存后，历史版本仍可运行。</p></div>`, '保存方案版本');
}

export async function plans({ view, refresh, active }) {
  const items = await api.plans();
  if (!active()) return;
  const canWrite = state.user.role === 'analyst';
  const latest = new Set(items.filter((item, index) => index === 0 || item.plan_key !== items[index - 1].plan_key)
    .map(item => item.id));
  const rows = items.map(plan => [
    `<b class="mono">${esc(plan.plan_key)}</b><small class="version">v${plan.version}</small><span class="subline">${esc(plan.label)}</span>`,
    `${BRANCH[plan.focus_branch]}<span class="subline">减 ${BRANCH[plan.control_branch]}</span>`,
    BASIS[plan.coefficient_ref], `<span class="mono">${esc(plan.date_from)}<br>${esc(plan.date_to)}</span>`,
    `${plan.min_samples} 张`, ...(canWrite ? [`<div class="row-actions"><button class="text-btn" data-use="${plan.id}">选用</button>
      ${latest.has(plan.id) ? `<button class="text-btn" data-revise="${plan.id}">另存版本</button>` : ''}</div>`] : []),
  ]);
  view.innerHTML = heading('比较口径', '对照组设置', '定下差额方向、样本日期和回归系数基准。每次修改保留一个可回溯版本。',
    canWrite ? '<button class="btn primary" data-new-plan>＋ 新建方案</button>' : '') +
    panel('方案版本', `${items.length} 个版本`, table(['方案 / 版本', '差额方向', '系数基准', '样本日期', '每点最低',
      ...(canWrite ? ['操作'] : [])], rows, '暂无版本。新建方案后即可提交一次运行。')) +
    '<aside class="method-note"><b>方向与基准</b><p>切换系数基准会重新分配构成差与系数差。只要两个网点和样本相同，合计仍等于两点的实际平均工时差。</p></aside>';
  const open = plan => openSheet(document.querySelector('#overlay'), editor(plan), async fields => {
    fields.min_samples = Number(fields.min_samples);
    if (plan) fields.base_version = plan.version;
    await api.savePlan(fields, plan?.plan_key);
    refresh();
  });
  if (canWrite) {
    view.querySelector('[data-new-plan]').onclick = () => open();
    view.querySelectorAll('[data-revise]').forEach(button => button.onclick = () =>
      open(items.find(item => item.id === Number(button.dataset.revise))));
    view.querySelectorAll('[data-use]').forEach(button => button.onclick = () => {
      state.planId = Number(button.dataset.use);
      go('runs');
    });
  }
}
