import { esc } from '../../utils/html.js';

export function field(label, name, value = '', attrs = '') {
  return `<label>${esc(label)}<input name="${esc(name)}" value="${esc(value)}" ${attrs}></label>`;
}

export function select(label, name, content) {
  return `<label>${esc(label)}<select name="${esc(name)}">${content}</select></label>`;
}

export function dialog(title, content, action) {
  return `<dialog class="sheet"><form>
    <header><h2>${esc(title)}</h2><button type="button" aria-label="关闭" data-close class="icon-btn">×</button></header>
    <div class="form-body">${content}</div>
    <footer><p role="alert" class="form-error" data-form-error></p><button type="button" data-close class="btn">取消</button>
    <button class="btn primary" type="submit">${esc(action)}</button></footer>
  </form></dialog>`;
}
