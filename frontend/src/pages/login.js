import { api } from '../api/workspace.js';
import { brand } from '../components/shell.js';
import { bindForm } from '../hooks/forms.js';
import { setSession } from '../stores/workspace.js';

export function login(root, enter) {
  root.innerHTML = `<main class="login-layout">
    <section class="login-art">
      <div class="brand">${brand}</div>
      <div class="umbrella-art" aria-hidden="true"><div class="canopy"></div><div class="spokes"></div><div class="shaft"></div><div class="handle"></div></div>
      <div class="art-caption"><span>北埠修伞铺 / 南桥修伞铺</span><span>返修计时工作台</span></div>
    </section>
    <section class="login-paper"><div class="login-content"><div class="kicker"><span></span>工票工作区</div>
      <h1>登录工作台</h1><p>核对两个网点的返修工票，拆解每张工票的平均工时差。</p>
      <form><label>账号<input name="username" autocomplete="username" placeholder="输入账号" required maxlength="32"></label>
      <label>口令<input name="password" type="password" autocomplete="current-password" placeholder="输入口令" required maxlength="128"></label>
      <p data-form-error role="alert" class="form-error"></p><button type="submit" class="btn primary">进入工作台 <span>↗</span></button></form>
    </div></section>
  </main>`;
  bindForm(root.querySelector('form'), async fields => {
    setSession(await api.login(fields));
    enter();
  });
}
