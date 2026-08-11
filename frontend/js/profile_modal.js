/**
 * profile_modal.js
 * Logica centralizada do modal de Perfil.
 *
 * Regras implementadas:
 * - Email FIXO (readonly) — alteracao somente via link enviado ao email.
 * - Foto so e salva no banco ao clicar "Salvar".
 *   Cancelar / fechar o modal reverte para a foto anterior.
 * - Botao "Redefinir E-mail" dispara POST /api/auth/recuperar-senha
 *   com o email atual (mesmo fluxo de "esqueci a senha").
 *
 * Uso: incluir este script apos api_client.js e app.js.
 * As paginas precisam ter o elemento <dialog id="modal-perfil"> no HTML.
 */
(function () {
    // Foto temporaria (apenas preview — nao salva ate clicar Salvar)
    var _fotoTemp = null;
    // Snapshot do estado ao abrir o modal
    var _inicial = null;

    /**
     * Abre o modal de perfil carregando os dados do localStorage.
     * Chamada por abrirModalPerfil() ou pelo App.init().
     */
    window.abrirModalPerfil = function () {
        var nome  = localStorage.getItem('auth_name')  || '';
        var email = localStorage.getItem('auth_email') || '';
        var foto  = localStorage.getItem('auth_photo') || '';

        var nomeEl  = document.getElementById('profile-nome');
        var emailEl = document.getElementById('profile-email');
        var imgEl   = document.getElementById('profile-photo');
        if (!nomeEl) return; // modal nao presente na pagina

        nomeEl.value  = nome;
        emailEl.value = email;

        // Foto: usar a salva ou gerar avatar por inicial
        imgEl.src = foto
            ? foto
            : ('https://ui-avatars.com/api/?name=' + encodeURIComponent(nome || 'U') +
               '&background=880D1E&color=fff&size=128');

        // Guardar snapshot — foto temporaria começa igual a salva
        _fotoTemp = foto;
        _inicial  = { nome: nome, email: email, foto: foto };

        document.getElementById('modal-perfil').showModal();
    };

    /**
     * Cancela edicao: reverte campos e foto para o estado anterior.
     * Chamada pelo botao Cancelar e pelo click no backdrop.
     */
    window.cancelarEdicaoPerfil = function () {
        if (_inicial) {
            document.getElementById('profile-nome').value  = _inicial.nome;
            document.getElementById('profile-email').value = _inicial.email;
            var imgEl = document.getElementById('profile-photo');
            imgEl.src = _inicial.foto
                ? _inicial.foto
                : ('https://ui-avatars.com/api/?name=' + encodeURIComponent(_inicial.nome || 'U') +
                   '&background=880D1E&color=fff&size=128');
        }
        _fotoTemp = _inicial ? _inicial.foto : null;
        document.getElementById('modal-perfil').close();
    };

    /**
     * Preview da foto selecionada — apenas na memoria, sem persistir.
     * Chamada pelo onchange do <input type="file">.
     */
    window.atualizarFotoPerfilPreview = function (input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('profile-photo').src = e.target.result;
                _fotoTemp = e.target.result; // armazena temporariamente
            };
            reader.readAsDataURL(input.files[0]);
        }
    };

    /**
     * Salva nome e, se a foto foi alterada, envia para o backend.
     * So executa persistencia ao clicar explicitamente em "Salvar".
     */
    window.salvarPerfil = async function () {
        var nome = document.getElementById('profile-nome').value.trim();
        try {
            // Foto: so salva se o usuario trocou (diferente do snapshot inicial)
            if (_fotoTemp && _fotoTemp !== _inicial.foto) {
                await API.Auth.updatePhoto(_fotoTemp);
                localStorage.setItem('auth_photo', _fotoTemp);
            }
            // Nome
            if (nome) localStorage.setItem('auth_name', nome);

            API.utils.mostrarToast('Perfil salvo com sucesso.', 'success');
            document.getElementById('modal-perfil').close();
        } catch (err) {
            API.utils.mostrarToast('Erro ao salvar perfil: ' + err.message, 'error');
        }
    };

    /**
     * Envia link de redefinicao de email para o email atual do usuario.
     * Usa o mesmo endpoint de "esqueci a senha".
     */
    window.redefinirEmailPerfil = async function () {
        var email = localStorage.getItem('auth_email') || '';
        if (!email) {
            API.utils.mostrarToast('E-mail nao encontrado. Faca login novamente.', 'error');
            return;
        }
        try {
            await API.Auth.sendPasswordReset(email);
            API.utils.mostrarToast(
                'Link de redefinicao enviado para ' + email + '. Verifique sua caixa de entrada.',
                'success'
            );
            document.getElementById('modal-perfil').close();
        } catch (err) {
            API.utils.mostrarToast('Erro ao enviar link: ' + err.message, 'error');
        }
    };

    // Fechar modal ao clicar no backdrop (quando o script e carregado apos o DOM)
    document.addEventListener('DOMContentLoaded', function () {
        var modal = document.getElementById('modal-perfil');
        if (modal) {
            modal.addEventListener('click', function (e) {
                if (e.target === modal) window.cancelarEdicaoPerfil();
            });
        }
    });
})();
