import { api } from '../api/workspace.js';
import { heading } from '../components/common/heading.js';
import { empty, panel } from '../components/common/panel.js';
import { status } from '../components/common/status.js';
import { table } from '../components/common/table.js';
import { BRANCH } from '../constants/domain.js';
import { bindForm } from '../hooks/forms.js';
import { state } from '../stores/workspace.js';
import { percent, runCode, signed } from '../utils/format.js';
import { esc } from '../utils/html.js';

export async function review({ id, view, active, refresh }) {
  const items = (await api.runs()).filter(run => run.status === 'completed');
  if (!active()) return;
  const header = heading('运营复核', '改进草案', '业务方复核差额口径和外推风险，保存下一步动作后发布。');
  if (!id) {
    view.innerHTML = header + panel('待阅工票', `${items.length} 条`, table(['运行', '方案版本', '复核状态', '打开'],
      items.map(run => [`<b class="mono">${runCode(run.id)}</b>`, `${esc(run.plan_key)} · v${run.version} / ${esc(run.label)}`,
        status(run.review_status), `<a class="text-btn" href="#/review/${run.id}">打开草案 ↗</a>`]),
      '暂无可阅草案。运行完成后，业务方可以填写改进动作。'));
    return;
  }
  if (!items.some(run => run.id === id)) {
    view.innerHTML = header + empty('暂无可阅草案', '可从草案目录选择有权限查看的运行。',
      '<a href="#/review" class="btn">返回草案目录</a>');
    return;
  }
  const { plan, result, draft } = await api.run(id);
  if (!active()) return;
  const canEdit = state.user.role === 'owner' && draft?.status !== 'published';
  const form = `<form class="draft-form"><label>下一步改进动作<textarea name="action_text" rows="5" minlength="5" maxlength="1000" required
    placeholder="例如先核对换骨和布损的共现样本，再决定是否调整排班。">${esc(draft?.action_text)}</textarea></label>
    <p role="alert" class="form-error" data-form-error></p><div class="row-actions"><button class="btn primary" type="submit">保存草案</button></div></form>`;
  const text = draft ? `<p class="draft-text">${esc(draft.action_text)}</p><p class="field-note">最后经办 ${esc(draft.edited_by)}</p>`
    : '<p class="draft-text">业务方尚未填写改进动作。</p>';
  view.innerHTML = header + `<div class="review-layout">${panel(`${runCode(id)} · ${plan.plan_key} v${plan.version}`, '', `
    <div class="review-body">${status(draft?.status)}${canEdit ? form : text}
    ${canEdit && draft ? '<div class="publish-row"><button class="btn" data-publish>发布给观察员 ↗</button><p>发布后，此草案和对应结果将进入观察员可阅范围。</p></div>' : ''}
    <p role="alert" class="inline-alert" data-review-error></p></div>`)}<aside class="review-slip">
    <h2>复核依据</h2><p>${BRANCH[plan.focus_branch]} − ${BRANCH[plan.control_branch]}</p>
    <dl><dt>实际工时差</dt><dd>${signed(result.gap)} 分钟/票</dd><dt>构成差 / 系数差</dt><dd>${signed(result.composition)} / ${signed(result.coefficient)}</dd>
    <dt>越界工票</dt><dd>${result.extrapolation.outside}/${result.extrapolation.total} · ${percent(result.extrapolation.share)}</dd></dl>
    <a class="text-btn" href="#/results/${id}">查看差额与拟合 ↗</a></aside></div>`;
  if (canEdit) bindForm(view.querySelector('form'), async fields => {
    await api.saveDraft(id, fields.action_text);
    state.notice = '改进草案已保存。';
    refresh();
  });
  const publish = view.querySelector('[data-publish]');
  if (publish) publish.onclick = async () => {
    publish.disabled = true;
    try {
      await api.publish(id);
      state.notice = '已发布给观察员。';
      refresh();
    } catch (error) {
      view.querySelector('[data-review-error]').textContent = error.message;
      publish.disabled = false;
    }
  };
}
