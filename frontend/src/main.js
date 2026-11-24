import { api } from './api/workspace.js';
import { empty } from './components/common/panel.js';
import { shell } from './components/shell.js';
import { login } from './pages/login.js';
import { plans } from './pages/plans.js';
import { results } from './pages/results.js';
import { review } from './pages/review.js';
import { runs } from './pages/runs.js';
import { tickets } from './pages/tickets.js';
import { route } from './router/routes.js';
import { setSession, state } from './stores/workspace.js';
import { esc } from './utils/html.js';

const root = document.querySelector('#app');
const pages = { tickets, plans, runs, results, review };
let epoch = 0;

function signOut() {
  setSession(null);
  history.replaceState(null, '', location.pathname);
  render();
}

async function render() {
  const current = ++epoch;
  if (!state.user) {
    login(root, render);
    return;
  }
  const { name, id } = route();
  root.innerHTML = shell(name, state.user);
  root.querySelector('[data-logout]').onclick = signOut;
  const view = root.querySelector('#view');
  const notice = state.notice;
  state.notice = '';
  view.innerHTML = '<p class="loading">正在读取工票…</p>';
  const active = () => current === epoch;
  try {
    await pages[name]({ id, view, refresh: render, active });
    if (active() && notice) view.insertAdjacentHTML('afterbegin', `<p class="notice" role="status">${esc(notice)}</p>`);
  } catch (error) {
    if (!active()) return;
    view.innerHTML = empty('读取工票失败', error.message, '<button class="btn" id="retry">重试</button>');
    view.querySelector('#retry').onclick = render;
  }
}

window.addEventListener('hashchange', render);
window.addEventListener('session-expired', signOut);
if (state.token) {
  try {
    state.user = await api.session();
  } catch {
    setSession(null);
  }
}
render();
