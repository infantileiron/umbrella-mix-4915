import { DRAFT_STATUS, RUN_STATUS } from '../../constants/domain.js';
import { esc } from '../../utils/html.js';

export function status(value) {
  return `<span class="status ${esc(value)}"><i></i>${esc(RUN_STATUS[value] || DRAFT_STATUS[value] || '待复核')}</span>`;
}
