// API Client - Centraliza comunicacao com o backend (com autenticacao)
const API_BASE = '/api';
const TOKEN_KEY = 'auth_token';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function setToken(token) { if (token) localStorage.setItem(TOKEN_KEY, token); else localStorage.removeItem(TOKEN_KEY); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }

async function apiRequest(url, method, data) {
    method = method || 'GET';
    const options = { method: method, headers: {} };
    const token = getToken();
    if (token) options.headers['Authorization'] = 'Bearer ' + token;

    let body;
    if (data instanceof FormData) {
        body = data;
    } else if (data != null) {
        options.headers['Content-Type'] = 'application/json';
        body = JSON.stringify(data);
    }
    options.body = body;

    const response = await fetch(API_BASE + url, options);
    let result;
    try {
        // 204 No Content não tem body — evitar tentar parsear JSON
        result = response.status === 204 ? {} : await response.json();
    } catch (e) { result = { message: response.statusText }; }
    if (!response.ok) {
        throw new Error((result && result.detail) || result.message || 'Erro na requisicao');
    }
    return result;
}

const PublicationAPI = {
    async create(p) { return apiRequest('/publications/', 'POST', p); },
    async list(params) {
        params = params || {};
        const q = new URLSearchParams(params).toString();
        return apiRequest('/publications/?' + q);
    },
    async get(id) { return apiRequest('/publications/' + id); },
    async update(id, p) { return apiRequest('/publications/' + id, 'PUT', p); },
    async delete(id) { return apiRequest('/publications/' + id, 'DELETE'); },
    async publishNow(id) { return apiRequest('/publications/' + id + '/publish', 'POST'); },
    async cancel(id) { return apiRequest('/publications/' + id + '/cancel', 'POST'); },
};

const PlatformAPI = {
    async list() { return apiRequest('/platforms/'); },
    async status(name) { return apiRequest('/platforms/' + name + '/status'); },
    async connect(name, credentials) { return apiRequest('/platforms/' + name + '/connect', 'POST', { credentials: credentials || {} }); },
    async disconnect(name) { return apiRequest('/platforms/' + name + '/disconnect', 'POST'); },
};

const AnalyticsAPI = {
    async overview() { return apiRequest('/analytics/overview'); },
    async byPlatform() { return apiRequest('/analytics/by-platform'); },
    async byMonth(months) { return apiRequest('/analytics/by-month?months=' + (months || 6)); },
    async successRate() { return apiRequest('/analytics/success-rate'); },
    async recentActivity() { return apiRequest('/analytics/recent-activity'); },
};

const AuthAPI = {
    async login(email, password) { return apiRequest('/auth/login', 'POST', { email, password }); },
    async register(name, email, password) { return apiRequest('/auth/register', 'POST', { name, email, password }); },
    async logout() { return apiRequest('/auth/logout', 'POST'); },
    async checkSession() { return apiRequest('/auth/session'); },
    async me() { return apiRequest('/auth/me'); },
    async sendPasswordReset(email) { return apiRequest('/auth/recuperar-senha', 'POST', { email }); },
    async resetPassword(token, password) { return apiRequest('/auth/redefinir-senha', 'POST', { token, password }); },
    async requestEmailChange(email, newEmail) {
        return apiRequest('/auth/request-email-change', 'POST', { email: email, new_email: newEmail });
    },
    async confirmEmailChange(token, newEmail) {
        return apiRequest('/auth/confirm-email-change', 'POST', { token: token, new_email: newEmail });
    },
    async updatePhoto(photo) { return apiRequest('/auth/update-photo', 'POST', { photo: photo }); },
    getToken: getToken, setToken: setToken, clearToken: clearToken,
};

const MediaAPI = {
    async upload(file, extra) {
        extra = extra || {};
        const form = new FormData();
        form.append('file', file);
        Object.keys(extra).forEach(function (k) { form.append(k, extra[k]); });
        return apiRequest('/media/', 'POST', form);
    },
    async list() { return apiRequest('/media/'); },
    async get(id) { return apiRequest('/media/' + id); },
    async update(id, fields) {
        const form = new FormData();
        Object.keys(fields).forEach(function (k) { form.append(k, fields[k]); });
        return apiRequest('/media/' + id, 'PUT', form);
    },
    async delete(id) { return apiRequest('/media/' + id, 'DELETE'); },
    downloadUrl(id) { return API_BASE + '/media/' + id + '/download'; },
};

function formatarData(data) {
    if (!data) return '';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function formatarHora(data) {
    if (!data) return '';
    const d = new Date(data);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}
function formatarDataHora(data) {
    if (!data) return '';
    return formatarData(data) + ' ' + formatarHora(data);
}
function mostrarToast(mensagem, tipo) {
    tipo = tipo || 'success';
    const toast = document.createElement('div');
    const corFundo = tipo === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800';
    const icone = tipo === 'success'
        ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>'
        : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>';
    toast.className = 'fixed top-4 right-4 ' + corFundo + ' border px-4 py-3 rounded-lg shadow-lg text-sm font-medium z-50 flex items-center gap-2';
    toast.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">' + icone + '</svg><span>' + mensagem + '</span>';
    document.body.appendChild(toast);
    setTimeout(function () { toast.style.transition = 'opacity .3s'; toast.style.opacity = '0'; setTimeout(function () { toast.remove(); }, 300); }, 3500);
}

window.API = {
    Base: { request: apiRequest, getToken: getToken, setToken: setToken, clearToken: clearToken },
    Publication: PublicationAPI,
    Platform: PlatformAPI,
    Analytics: AnalyticsAPI,
    Auth: AuthAPI,
    Media: MediaAPI,
    utils: { formatarData: formatarData, formatarHora: formatarHora, formatarDataHora: formatarDataHora, mostrarToast: mostrarToast, getToken: getToken, setToken: setToken, clearToken: clearToken },
};