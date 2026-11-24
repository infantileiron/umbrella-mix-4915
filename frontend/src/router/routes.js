export const links = [
  ['tickets', '▤', '网点任务账'], ['plans', '⊞', '对照组设置'], ['runs', '▷', '运行工票'],
  ['results', '◫', '差额拆解'], ['review', '◇', '改进草案'],
];

export function route() {
  const [name, id] = location.hash.replace(/^#\/?/, '').split('/');
  return { name: links.some(item => item[0] === name) ? name : 'tickets', id: /^\d+$/.test(id) ? Number(id) : null };
}

export function go(name, id) {
  location.hash = `/${name}${id ? `/${id}` : ''}`;
}
