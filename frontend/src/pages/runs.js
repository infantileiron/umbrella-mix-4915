import { api } from '../api/workspace.js';
import { select } from '../components/common/form.js';
import { heading } from '../components/common/heading.js';
import { empty, panel } from '../components/common/panel.js';
import { status } from '../components/common/status.js';
import { table } from '../components/common/table.js';
import { BASIS, BRANCH } from '../constants/domain.js';
import { bindForm } from '../hooks/forms.js';
import { poll } from '../hooks/poll.js';
import { state } from '../stores/workspace.js';
import { localTime, runCode } from '../utils/format.js';
import { esc } from '../utils/html.js';

function choices(plans) {
  return plans.map(plan => `<option value="${plan.id}"${plan.id === state.planId ? ' selected' : ''}>${esc(plan.plan_key)}
    · v${plan.version} · ${esc(plan.label)}</option>`).join('');
}

function queueTable(items) {
  return table(['运行工票', '方案版本', '提交时间', '计算状态', '复核状态', '查看'], items.map(run => [
    `<b class="mono">${runCode(run.id)}</b>`, `<b>${esc(run.plan_key)} · v${run.version}</b><span class="subline">${esc(run.label)}</span>`,
    esc(localTime(run.created_at)), `${status(run.status)}${run.failure ? `<span class="subline failure">${esc(run.failure)}</span>` : ''}`,
    run.status === 'completed' ? status(run.review_status) : '—',
    run.status === 'completed' ? `<a class="text-btn" href="#/results/${run.id}">查看拆解 ↗</a>` : '—',
  ]), '暂无可阅运行。提交方案后可在这里查看计算进度。', 'run-table');
}

export async function runs({ view, active, refresh }) {
  const canWrite = state.user.role === 'analyst';
  const [plans, items] = await Promise.all([canWrite ? api.plans() : [], api.runs()]);
  if (!active()) return;
  const setup = plans.length ? `<section class="run-console"><form class="run-form">
    <div class="field-grow">${select('选择已保存的方案版本', 'plan_id', choices(plans))}<p id="selected-plan"></p></div>
    <button class="btn primary" type="submit">提交拆解运行 ↗</button><p role="alert" class="form-error" data-form-error></p>
    </form><div class="run-side"><b>运行时封存</b><p>方案、逐票样本与修订号共同写入快照。之后改工票，已提交的运行仍可追溯。</p></div></section>`
    : empty('先设置对照组', '保存一个比较方案版本后，就可以提交运行。', '<a class="btn" href="#/plans">打开对照组设置</a>');
  view.innerHTML = heading('计算队列', '运行工票', '从已保存的口径发起计算，核对快照、进度与待补正记录。',
    '<button class="btn" data-reload>刷新运行</button>') + (canWrite ? setup : '') +
    panel('运行记录', '', `<p class="inline-alert" data-poll-error></p><div id="run-items">${queueTable(items)}</div>`);
  const showQueue = entries => {
    view.querySelector('#run-items').innerHTML = queueTable(entries);
  };
  const pending = entries => entries.some(run => ['queued', 'running'].includes(run.status));
  const watch = () => poll(async () => {
    const entries = await api.runs();
    if (active()) showQueue(entries);
    return pending(entries);
  }, active);
  if (pending(items)) watch();
  view.querySelector('[data-reload]').onclick = refresh;
  const form = view.querySelector('form');
  if (form) {
    const display = () => {
      const plan = plans.find(item => item.id === Number(form.elements.plan_id.value));
      state.planId = plan.id;
      view.querySelector('#selected-plan').textContent = `${BRANCH[plan.focus_branch]} − ${BRANCH[plan.control_branch]} · ${BASIS[plan.coefficient_ref]} · 每点 ≥ ${plan.min_samples} 张`;
    };
    form.elements.plan_id.onchange = display;
    display();
    bindForm(form, async () => {
      await api.submitRun(state.planId);
      state.notice = '运行已提交。';
      refresh();
    });
  }
}
