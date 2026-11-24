from datetime import date, timedelta
from itertools import product

USERS = (
    ('owner', '陆缃 · 运营复核', 'RainOwner2026!', 'owner'),
    ('analyst', '程砚 · 工时分析', 'RainAnalyst2026!', 'analyst'),
    ('observer', '季禾 · 站点巡阅', 'RainView2026!', 'observer'),
)
PLAN = ('RAIN-W46', 1, '雨后第一周 · 跨网点比较', 'south', 'north', 'control',
        '2026-11-09', '2026-11-15', 12, 'analyst')
NOTES = ('收伞后核验开合', '校直后复测伞骨', '修补区已压边', '更换铆钉后试撑')


def demo_tickets():
    start = date(2026, 11, 9)
    for branch, prefix, shift, intercept, slopes in (
        ('north', 'BE', 0, 10, (3, 2, 4)),
        ('south', 'NQ', 1, 14, (4, 3, 5)),
    ):
        for index, (ribs, fabric, mechanism) in enumerate(product(range(1, 5), range(1, 5), range(2)), 1):
            ribs, fabric = ribs + shift, fabric + shift
            minutes = intercept + ribs * slopes[0] + fabric * slopes[1] + mechanism * slopes[2]
            yield (f'{prefix}-W46-{index:02d}', branch, start + timedelta(days=(index - 1) % 7),
                   ribs, fabric, mechanism, minutes, NOTES[(index - 1) % len(NOTES)])
