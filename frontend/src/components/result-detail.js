import { panel } from './common/panel.js';
import { table } from './common/table.js';
import { BRANCH, TERMS, TERM_UNIT } from '../constants/domain.js';
import { number, percent, signed } from '../utils/format.js';

const quantity = value => `<strong class="mono">${signed(value)}</strong><small> 分钟/票</small>`;

function factorTable(result) {
  return table(['工序项', 'A 均值', 'B 均值', 'A 系数', 'B 系数', '构成差', '系数差'], result.terms.map(term => {
    const a = result.focus.terms[term.term], b = result.control.terms[term.term];
    return [`<b>${TERMS[term.term]}</b><span class="unit">${TERM_UNIT[term.term]}</span>`, number(a.mean), number(b.mean),
      number(a.coefficient), number(b.coefficient), `<b class="mono warm">${signed(term.composition)}</b>`,
      `<b class="mono cool">${signed(term.coefficient)}</b>`];
  }), undefined, 'factors');
}

function supportBox(result) {
  const support = result.extrapolation;
  const rows = Object.entries(TERMS).filter(([key]) => key !== 'intercept').map(([key, label]) => {
    const values = support.terms[key];
    return `<li><span>${label} ${values.min}–${values.max}</span><b>${values.outside} 张越界</b></li>`;
  }).join('');
  return `<aside class="support ${support.outside ? 'warning' : ''}">
    <div class="support-head"><span>${support.outside ? '⚑ 外推提醒' : '范围核对'}</span><b class="mono">${percent(support.share)}</b></div>
    <p><b>${BRANCH[support.evaluated_branch]} ${support.outside}/${support.total} 张</b>至少一项工序超出${BRANCH[support.basis_branch]}的观测范围。</p>
    <ul>${rows}</ul>${support.outside ? '<p class="support-action">复核越界工票后，再用基准系数估算类似返修。</p>' : ''}</aside>`;
}

function fitTable(result) {
  const a = result.focus, b = result.control;
  return table(['拟合摘要', '工票', '平均工时', '秩', '条件数', 'R²', 'RMSE'], [a, b].map(item => [
    `<b>${BRANCH[item.branch]}</b>`, item.n, number(item.mean_minutes), `${item.rank}/4`, number(item.condition),
    number(item.r_squared, 3), number(item.rmse, 3),
  ]));
}

export function resultDetail(result) {
  const a = result.focus, b = result.control;
  const maximum = Math.max(Math.abs(result.gap), Math.abs(result.composition), Math.abs(result.coefficient), 0.01);
  const metrics = [
    ['实际工时差', 'total', result.gap, `${number(a.mean_minutes)} − ${number(b.mean_minutes)}`],
    ['构成差', 'composition', result.composition, '工序数量与分布贡献'],
    ['系数差', 'coefficient', result.coefficient, '截距与回归斜率贡献'],
  ];
  return `<section class="result-strip" aria-label="总差、构成差与系数差">${metrics.map(([label, type, value, note]) => {
    const width = Math.abs(value) / maximum * 50;
    return `<article class="result-metric ${type}"><h2>${label}</h2><div class="value">${quantity(value)}</div>
      <div class="scale" aria-hidden="true"><i style="left:${value < 0 ? 50 - width : 50}%;width:${width}%"></i></div><p>${note}</p></article>`;
  }).join('')}</section>
  <div class="conservation"><span><b>✓ 差额守恒</b>　${signed(result.gap)} = ${signed(result.composition)} + (${signed(result.coefficient)})<small>　显示值四舍五入</small></span>
  <span class="mono">残差 ${result.remainder.toExponential(2)}</span></div>
  <div class="analysis-layout">${panel('逐工序贡献', '分钟 / 票', factorTable(result))}${supportBox(result)}</div>
  <details class="fit-details"><summary>展开拟合摘要与反事实均值 <span class="mono">${number(result.counterfactual)} 分钟/票</span></summary>
  ${fitTable(result)}<p>反事实均值用${BRANCH[result.extrapolation.basis_branch]}的系数，估算${BRANCH[result.extrapolation.evaluated_branch]}这批工票的平均工时。系数差也可能包含工具、人员与未记工序的差异。</p></details>`;
}
