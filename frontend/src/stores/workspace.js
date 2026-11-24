const storedToken = sessionStorage.getItem('umbrella-token');

export const state = {
  token: storedToken,
  /** @type {import('../types/domain.js').User | null} */
  user: null,
  ledger: { page: 1, branch: '' },
  planId: null,
  notice: '',
};

export function setSession(session) {
  state.token = session?.token ?? null;
  state.user = session?.user ?? null;
  if (state.token) sessionStorage.setItem('umbrella-token', state.token);
  else {
    sessionStorage.removeItem('umbrella-token');
    state.ledger = { page: 1, branch: '' };
    state.planId = null;
    state.notice = '';
  }
}
