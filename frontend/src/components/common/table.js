import { esc } from '../../utils/html.js';

export function table(headers, rows, empty = '暂无记录。', className = '') {
  return `<div class="table-wrap ${esc(className)}"><table>
    <thead><tr>${headers.map(header => `<th scope="col">${esc(header)}</th>`).join('')}</tr></thead>
    <tbody>${rows.length ? rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')
      : `<tr><td colspan="${headers.length}" class="empty-cell">${esc(empty)}</td></tr>`}</tbody>
  </table></div>`;
}
