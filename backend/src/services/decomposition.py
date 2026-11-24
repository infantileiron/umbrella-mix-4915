import numpy as np

from src.constants.domain import BRANCH_LABEL, FEATURES, METHOD, TERMS


class AnalysisError(ValueError):
    pass


def _fit(rows, branch, minimum):
    samples = [row for row in rows if row['branch'] == branch]
    count = len(samples)
    if count < minimum:
        raise AnalysisError(f'{BRANCH_LABEL[branch]}只有 {count} 张工票，本方案要求至少 {minimum} 张。请补录工票或另存日期版本。')
    values = np.array([[row[key] for key in FEATURES] for row in samples], dtype=float)
    design = np.column_stack((np.ones(count), values))
    response = np.array([row['minutes'] for row in samples], dtype=float)
    beta, _, rank, singular_values = np.linalg.lstsq(design, response, rcond=None)
    if rank != len(TERMS):
        raise AnalysisError(f'{BRANCH_LABEL[branch]}特征不满秩（{rank}/{len(TERMS)}）。请补录工序组合更丰富的工票。')
    residuals = response - design @ beta
    sse = float(residuals @ residuals)
    centered = response - response.mean()
    sst = float(centered @ centered)
    return design, beta, dict(
        branch=branch, n=count, mean_minutes=float(response.mean()),
        rank=int(rank), condition=float(singular_values[0] / singular_values[-1]),
        r_squared=1 - sse / sst if sst else None, rmse=float(np.sqrt(sse / count)),
        terms={key: {'mean': float(design[:, index].mean()), 'coefficient': float(beta[index])}
               for index, key in enumerate(TERMS)},
    )


def _support(evaluated, basis):
    low, high = basis.min(axis=0), basis.max(axis=0)
    outside = (evaluated < low) | (evaluated > high)
    terms = {key: {'outside': int(outside[:, index].sum()), 'min': int(low[index]), 'max': int(high[index])}
             for index, key in enumerate(FEATURES, start=1)}
    count = int(outside.any(axis=1).sum())
    return dict(outside=count, total=len(evaluated), share=count / len(evaluated), terms=terms)


def analyze(snapshot):
    plan, rows = snapshot['plan'], snapshot['tickets']
    xa, ba, a = _fit(rows, plan['focus_branch'], plan['min_samples'])
    xb, bb, b = _fit(rows, plan['control_branch'], plan['min_samples'])
    ma, mb = xa.mean(axis=0), xb.mean(axis=0)
    use_control = plan['coefficient_ref'] == 'control'
    basis = bb if use_control else ba
    composition_terms = (ma - mb) * basis
    coefficient_terms = (ma if use_control else mb) * (ba - bb)
    gap = a['mean_minutes'] - b['mean_minutes']
    composition, coefficient = float(composition_terms.sum()), float(coefficient_terms.sum())
    remainder = gap - composition - coefficient
    if abs(remainder) > 1e-8:
        raise AnalysisError('两项之和未通过守恒检查，请核查样本。')
    return dict(
        method=METHOD, gap=gap, composition=composition, coefficient=coefficient, remainder=remainder,
        focus=a, control=b, terms=[dict(term=key, composition=float(composition_terms[index]),
                                       coefficient=float(coefficient_terms[index]))
                                  for index, key in enumerate(TERMS)],
        counterfactual=float(ma @ bb if use_control else mb @ ba),
        extrapolation={**(_support(xa, xb) if use_control else _support(xb, xa)),
                       'evaluated_branch': a['branch'] if use_control else b['branch'],
                       'basis_branch': b['branch'] if use_control else a['branch']},
    )
