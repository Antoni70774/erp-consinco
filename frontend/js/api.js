// Lê a URL do backend a partir de js/config.js (ajustável por instalação/cliente).
// Fallback: se config.js não foi carregado, tenta mesmo host na porta 8000 (uso local).
const API_BASE = (window.ERP_CONFIG && window.ERP_CONFIG.API_BASE)
  ? window.ERP_CONFIG.API_BASE.replace(/\/$/, '')
  : `${window.location.protocol}//${window.location.hostname}:8000`;

const API = {
  async _request(method, path, body) {
    const token = localStorage.getItem('erp_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      localStorage.removeItem('erp_token');
      localStorage.removeItem('erp_usuario');
      if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
        window.location.href = 'index.html';
      }
      throw new Error('Sessão expirada. Faça login novamente.');
    }

    if (res.status === 204) return null;

    let data = null;
    try { data = await res.json(); } catch (e) { /* corpo vazio */ }

    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || `Erro ${res.status}`;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  },

  get(path) { return this._request('GET', path); },
  post(path, body) { return this._request('POST', path, body); },
  put(path, body) { return this._request('PUT', path, body); },
  del(path) { return this._request('DELETE', path); },

  async login(login, senha) {
    return this._request('POST', '/api/auth/login', { login, senha });
  },
};
