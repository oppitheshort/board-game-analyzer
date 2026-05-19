import { injectPopupStyles } from './styles';

injectPopupStyles();

const app = document.getElementById('app')!;

interface PopupState {
  token: string | null;
  email: string | null;
  isAuthenticated: boolean;
  mode: string;
  isWatching: boolean;
  isConnected: boolean;
}

let state: PopupState = {
  token: null,
  email: null,
  isAuthenticated: false,
  mode: 'bga',
  isWatching: false,
  isConnected: false,
};

function send(msg: Record<string, any>): Promise<any> {
  return chrome.runtime.sendMessage(msg);
}

function renderLogin(): void {
  app.innerHTML = `
    <div class="popup-header"><h1>Game Analyzer</h1></div>
    <div class="popup-body">
      <div class="tab-bar">
        <div class="tab active" id="tab-login">Login</div>
        <div class="tab" id="tab-register">Register</div>
      </div>
      <div style="margin-top:12px">
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="email" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" id="password" placeholder="Min 8 characters">
        </div>
        <div id="error" class="error" style="display:none"></div>
        <button class="btn btn-primary" id="submit-btn">Login</button>
      </div>
    </div>
  `;

  let isLogin = true;
  const tabLogin = document.getElementById('tab-login')!;
  const tabRegister = document.getElementById('tab-register')!;
  const submitBtn = document.getElementById('submit-btn')!;
  const errorEl = document.getElementById('error')!;

  tabLogin.addEventListener('click', () => {
    isLogin = true;
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    submitBtn.textContent = 'Login';
  });

  tabRegister.addEventListener('click', () => {
    isLogin = false;
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    submitBtn.textContent = 'Register';
  });

  submitBtn.addEventListener('click', async () => {
    const email = (document.getElementById('email') as HTMLInputElement).value.trim();
    const password = (document.getElementById('password') as HTMLInputElement).value;
    errorEl.style.display = 'none';

    if (!email || !password) {
      errorEl.textContent = 'Email and password required';
      errorEl.style.display = 'block';
      return;
    }

    submitBtn.textContent = 'Loading...';
    (submitBtn as HTMLButtonElement).disabled = true;

    const type = isLogin ? 'LOGIN' : 'REGISTER';
    const resp = await send({ type, payload: { email, password } });

    if (resp?.type === 'AUTH_SUCCESS') {
      state.token = resp.payload.token;
      state.email = resp.payload.email;
      state.isAuthenticated = true;
      renderDashboard();
    } else if (resp?.type === 'AUTH_ERROR') {
      errorEl.textContent = resp.payload.message;
      errorEl.style.display = 'block';
      submitBtn.textContent = isLogin ? 'Login' : 'Register';
      (submitBtn as HTMLButtonElement).disabled = false;
    }
  });
}

function renderDashboard(): void {
  const modeActive = (m: string) => m === state.mode ? 'active' : '';
  const watchClass = state.isWatching ? 'on' : '';

  app.innerHTML = `
    <div class="popup-header"><h1>Game Analyzer</h1></div>
    <div class="popup-body">
      <div class="user-info">${state.email || 'Logged in'}</div>

      <div class="section-title">Detection Mode</div>
      <div class="mode-selector">
        <div class="mode-btn ${modeActive('bga')}" data-mode="bga">BGA Integration</div>
        <div class="mode-btn ${modeActive('screen_capture')}" data-mode="screen_capture">Screen Capture</div>
      </div>

      <div class="section-title">Analysis</div>
      <div class="status-row">
        <label class="toggle-label" style="width:100%">
          <span>Watch Game</span>
          <div class="toggle-switch ${watchClass}" id="watch-toggle"></div>
        </label>
      </div>

      <div class="section-title">Connection</div>
      <div class="status-row">
        <span><span class="status-indicator ${state.isConnected ? 'on' : 'off'}"></span>Backend</span>
        <span style="color:#7f8c8d">${state.isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>

      <button class="btn btn-danger" id="logout-btn">Logout</button>
    </div>
  `;

  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const mode = (btn as HTMLElement).dataset.mode!;
      await send({ type: 'SET_MODE', payload: mode });
      state.mode = mode;
      renderDashboard();
    });
  });

  document.getElementById('watch-toggle')!.addEventListener('click', async () => {
    await send({ type: 'TOGGLE_WATCHING' });
    state.isWatching = !state.isWatching;
    renderDashboard();
  });

  document.getElementById('logout-btn')!.addEventListener('click', async () => {
    await send({ type: 'LOGOUT' });
    state = { token: null, email: null, isAuthenticated: false, mode: 'bga', isWatching: false, isConnected: false };
    renderLogin();
  });
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'STATE_UPDATE') {
    state = { ...state, ...msg.payload };
    if (state.isAuthenticated) renderDashboard();
  }
});

async function init(): Promise<void> {
  const resp = await send({ type: 'GET_STATE' });
  if (resp?.type === 'STATE_UPDATE' && resp.payload) {
    state = { ...state, ...resp.payload };
    if (state.isAuthenticated || state.token) {
      renderDashboard();
    } else {
      renderLogin();
    }
  } else {
    renderLogin();
  }
}

init();
