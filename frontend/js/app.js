/* app.js - Logica compartilhada: autenticacao, header, modais, suporte */
(function () {
    'use strict';
    const TOKEN_KEY = 'auth_token';

    function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
    function setToken(t) { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); }
    function clearToken() { localStorage.removeItem(TOKEN_KEY); }

    // Salva estado do usuario no localStorage (usado por google/login)
    function persistUser(token, user) {
        setToken(token);
        if (user) {
            localStorage.setItem('auth_name', user.name || '');
            localStorage.setItem('auth_email', user.email || '');
            localStorage.setItem('auth_photo', user.profile_photo || '');
            localStorage.setItem('auth_id', user.id || '');
        }
    }

    // Alias retrocompatível: usado por login.html e cadastro.html
    function persistirAuth(data) {
        const user = (data && data.user) || {};
        if (data && data.token) setToken(data.token);
        if (user.name) localStorage.setItem('auth_name', user.name);
        if (user.email) localStorage.setItem('auth_email', user.email);
        if (user.profile_photo) {
            localStorage.setItem('auth_photo', user.profile_photo);
        } else {
            localStorage.removeItem('auth_photo');
        }
        localStorage.setItem('auth_user', JSON.stringify(user));
    }

    function getUserFromStorage() {
        return {
            id: localStorage.getItem('auth_id') || '',
            name: localStorage.getItem('auth_name') || '',
            email: localStorage.getItem('auth_email') || '',
            profile_photo: localStorage.getItem('auth_photo') || ''
        };
    }

    function limparQuery() {
        if (window.location.search) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    // Consome token recebido via GET (Google OAuth callback)
    function consumeGoogleToken() {
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        if (!token) return false;
        persistUser(token, {
            id:            params.get('id')    || '',
            name:          params.get('name')  || '',
            email:         params.get('email') || '',
            profile_photo: params.get('photo') || ''
        });
        limparQuery();
        return true;
    }

    const PUBLIC_PAGES = ['login.html', 'cadastro.html', 'esqueci-senha.html',
                          'redefinir-senha.html', 'redefinir-email.html', 'onboarding.html'];

    function currentPage() {
        return window.location.pathname.split('/').pop() || 'index.html';
    }

    // Exige autenticacao; redireciona ao login se nao autenticado
    function requireAuth() {
        const page = currentPage();
        if (PUBLIC_PAGES.indexOf(page) !== -1) return true;
        const token = getToken();
        if (!token) {
            window.location.href = 'login.html?next=' + encodeURIComponent(window.location.href);
            return false;
        }
        return true;
    }

    // Carrega usuario autenticado e preenche o header (se elementos existirem)
    async function loadUser() {
        const token = getToken();
        if (!token) {
            if (PUBLIC_PAGES.indexOf(currentPage()) === -1) {
                window.location.href = 'login.html';
            }
            return null;
        }
        try {
            const r = await API.Auth.me();
            if (!r.authenticated) {
                // Sessão expirou no servidor (reinício, etc.)
                // Se há dados locais, manter o usuário na tela em vez de redirecionar
                const stored = getUserFromStorage();
                if (stored.name || stored.email) {
                    renderHeader(stored);
                    return stored;
                }
                clearToken();
                if (PUBLIC_PAGES.indexOf(currentPage()) === -1) {
                    window.location.href = 'login.html';
                }
                return null;
            }
            const user = r.user;
            persistUser(token, user);
            renderHeader(user);
            return user;
        } catch (e) {
            // Servidor indisponível — usa dados locais sem redirecionar
            const u = getUserFromStorage();
            renderHeader(u);
            return u;
        }
    }

    function renderHeader(user) {
        const avatar = document.getElementById('user-avatar');
        const nameEl = document.getElementById('user-name');
        const emailEl = document.getElementById('user-email');
        if (nameEl && user.name) nameEl.textContent = user.name;
        if (emailEl && user.email) emailEl.textContent = user.email;
        if (avatar) {
            if (user.profile_photo) {
                avatar.src = user.profile_photo;
                avatar.classList.remove('bg-neutral-300');
            } else {
                avatar.src = avatarFallback(user.name || user.email || 'U');
                avatar.classList.add('bg-neutral-300');
            }
        }
        const inicialEl = document.getElementById('user-inicial');
        if (inicialEl) {
            const n = (user.name || user.email || 'U');
            inicialEl.textContent = n.charAt(0).toUpperCase();
        }
    }

    function avatarFallback(nameOrEmail) {
        const initial = (nameOrEmail || 'U').charAt(0).toUpperCase();
        const code = encodeURIComponent(initial);
        return 'https://ui-avatars.com/api/?name=' + code + '&background=880D1E&color=fff&size=64';
    }

    // Foto de perfil: persiste SOMENTE quando o usuario clicar em Salvar.
    // `onPreview(photo)` atualiza a imagem temporariamente; `onSave(photo)` persiste.
    window.App = {
        getToken: getToken, setToken: setToken, clearToken: clearToken,
        persistUser: persistUser, persistirAuth: persistirAuth,
        getUserFromStorage: getUserFromStorage,
        consumeGoogleToken: consumeGoogleToken, requireAuth: requireAuth,
        loadUser: loadUser, renderHeader: renderHeader,
        avatarFallback: avatarFallback,

        // Logout
        wireLogout: function () {
            const btn = document.getElementById('logout-btn');
            if (btn) btn.onclick = async function () {
                try { await API.Auth.logout(); } catch (e) { /* ignora */ }
                clearToken();
                window.location.href = 'login.html?logout=true';
            };
        },

        // Fecha <details> abertos ao clicar fora deles (suporte, 3 risquinhos, etc.)
        setupClickOutsideDetails: function () {
            document.addEventListener('click', function (e) {
                const details = document.querySelectorAll('details');
                details.forEach(function (d) {
                    if (d.open && d !== e.target && !d.contains(e.target)) {
                        d.removeAttribute('open');
                    }
                });
            });
        },

        // Redireciona links de suporte (Discord) para DM individual
        setupDiscordLinks: function (map) {
            map = map || {
                'janquinas': '644151758859272228',
                'aatrox': '400121880385683457'
            };
            document.querySelectorAll('[data-discord-user]').forEach(function (el) {
                const key = (el.getAttribute('data-discord-user') || '').toLowerCase();
                const id = map[key];
                if (id) el.href = 'https://discord.com/channels/@me/' + id;
            });
        },

        // Fecha modais ao clicar no backdrop
        setupModals: function () {
            document.querySelectorAll('dialog').forEach(function (d) {
                d.addEventListener('click', function (e) {
                    if (e.target === d) {
                        const closeFn = d.dataset.closeFn;
                        if (typeof closeFn === 'function') closeFn();
                        else d.close();
                    }
                });
                // botao fechar padrao
                const fc = d.querySelector('[data-close]');
                if (fc) fc.onclick = function () { d.close(); };
            });
        },

        init: function () {
            if (!requireAuth()) return;
            consumeGoogleToken();
            loadUser();
            App.wireLogout();
            App.setupClickOutsideDetails();
            App.setupDiscordLinks();
            App.setupModals();
        }
    };

    // Retrocompatibilidade: login.html e cadastro.html chamam persistirAuth() no escopo global
    window.persistirAuth = persistirAuth;

    // ---------------------------------------------------------------------
    // Configuracoes do usuario — centralizadas (antes duplicadas em 5 HTMLs)
    // ---------------------------------------------------------------------
    // Carrega preferencias salvas em localStorage para o modal de configuracoes
    window.carregarConfiguracoes = function () {
        const cfg = JSON.parse(localStorage.getItem('app_config') || '{}');
        const emailChk = document.getElementById('cfg-email-notif');
        const pushChk  = document.getElementById('cfg-push-notif');
        const failChk  = document.getElementById('cfg-fail-alert');
        if (emailChk) emailChk.checked = cfg.emailNotif !== false;
        if (pushChk)  pushChk.checked  = cfg.pushNotif  === true;
        if (failChk)  failChk.checked  = cfg.failAlert  !== false;
    };

    // Salva preferencias e fecha o modal (usado em onclick dos HTMLs)
    window.salvarConfiguracoes = function () {
        const emailChk = document.getElementById('cfg-email-notif');
        const pushChk  = document.getElementById('cfg-push-notif');
        const failChk  = document.getElementById('cfg-fail-alert');
        localStorage.setItem('app_config', JSON.stringify({
            emailNotif: emailChk ? emailChk.checked : true,
            pushNotif:  pushChk  ? pushChk.checked  : false,
            failAlert:  failChk  ? failChk.checked  : true,
        }));
        const modal = document.getElementById('modal-config');
        if (modal) modal.close();
        if (window.API && API.utils) API.utils.mostrarToast('Configurações salvas!', 'success');
    };
})();