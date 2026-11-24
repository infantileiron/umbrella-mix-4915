import { api } from '../api/workspace.js';
import { heading } from '../components/common/heading.js';
import { empty } from '../components/common/panel.js';
import { resultDetail } from '../components/result-detail.js';
import { BASIS, BRANCH } from '../constants/domain.js';
import { state } from '../stores/workspace.js';
import { localTime, runCode } from '../utils/format.js';
import { esc } from '../utils/html.js';

const ARTIFACT = {
  available: point => `<span class="artifact-state ready">原件已可用${point.available_at ? ` · ${esc(localTime(point.available_at))}` : ''}</span>`,
  pending: () => '<span class="artifact-state pending">原件待补齐 · 取件时当场生成</span>',
  unrecoverable: point => `<span class="artifact-state bad">原件无法恢复</span>
    <small class="artifact-why">${esc(point.message || '封存内容与发布指纹不符。')}</small>`,
};

function artifactControl(run) {
  const point = run.artifact;
  if (!point) return '';
  const sha = esc(point.expected_sha256.slice(0, 10));
  const download = point.state === 'unrecoverable'
    ? `<span class="text-btn disabled" aria-disabled="true" title="${esc(point.expected_sha256)}">原件 ${sha}</span>`
    : `<button class="text-btn" data-download="snapshot" title="${esc(point.expected_sha256)}">原件 ${sha} ↓</button>`;
  return `${download}${ARTIFACT[point.state](point)}`;
}

export async function results({ id, view, active, refresh }) {
  const completed = (await api.runs()).filter(run => run.status === 'completed');
  if (!active()) return;
  const chosen = id ? completed.find(run => run.id === id) : completed[0];
  if (!chosen) {
    view.innerHTML = heading('差额复算', '差额拆解', '按工序核对平均工时差和外推范围。') + empty('暂无可阅拆解',
      '计算完成后可从运行记录打开结果。观察员可阅已发布版本。', '<a class="btn" href="#/runs">查看运行工票</a>');
    return;
  }
  const run = await api.run(chosen.id);
  if (!active()) return;
  const { plan, result } = run;
  view.innerHTML = heading('差额复算', '差额拆解',
    `${BRANCH[plan.focus_branch]}（A）减 ${BRANCH[plan.control_branch]}（B） · ${BASIS[plan.coefficient_ref]}为基准`,
    '<button class="btn primary" data-download="csv">导出 CSV ↓</button>') + `<div class="result-meta">
    <label class="result-picker">运行工票<select name="result_id">${completed.map(item => `<option value="${item.id}"${item.id === run.id ? ' selected' : ''}>${runCode(item.id)} · ${esc(item.plan_key)} v${item.version}</option>`).join('')}</select></label>
    <span class="mono">${esc(plan.date_from)}  →  ${esc(plan.date_to)}</span><span>共 ${run.sample_count} 张</span>
    ${artifactControl(run)}
    <a class="text-btn" href="#/review/${run.id}">查看改进草案 ↗</a></div>
    <p data-export-error role="alert" class="inline-alert"></p>` + resultDetail(result);
  view.querySelector('[name=result_id]').onchange = event => { location.hash = `#/results/${event.target.value}`; };
  view.querySelectorAll('[data-download]').forEach(button => button.onclick = async () => {
    const message = view.querySelector('[data-export-error]');
    message.textContent = '';
    const snapshot = button.dataset.download === 'snapshot';
    try {
      if (snapshot) {
        await api.exportSnapshot(run.id);
        if (run.artifact?.state !== 'available') {
          state.notice = '原件已补齐并通过指纹核对。';
          refresh();
        }
      } else {
        await api.exportResult(run.id);
      }
    } catch (error) {
      message.textContent = error.message;
    }
  });
}
