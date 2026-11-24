export const number = (value, digits = 2) => value == null ? '—' : Number(value).toFixed(digits);
export const signed = value => Math.abs(value) < 0.005 ? '0.00' : `${value < 0 ? '−' : '+'}${number(Math.abs(value))}`;
export const percent = value => `${number(value * 100, 1)}%`;
export const runCode = id => `R-${String(id).padStart(3, '0')}`;
export const localTime = value => value ? new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
}).format(new Date(`${value.replace(' ', 'T')}${value.endsWith('Z') || value.includes('+') ? '' : 'Z'}`)) : '—';
