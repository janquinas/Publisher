// UX - Utilitários de experiência do usuário

// Mostrar loading em um botão
function setLoading(button, isLoading, text = 'Carregando...') {
    if (isLoading) {
        button.dataset.originalText = button.textContent;
        button.textContent = text;
        button.disabled = true;
        button.classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
        button.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Mostrar toast de erro
function mostrarErro(mensagem) {
    if (window.API && window.API.utils) {
        window.API.utils.mostrarToast(mensagem, 'error');
    } else {
        alert(mensagem);
    }
}

// Mostrar toast de sucesso
function mostrarSucesso(mensagem) {
    if (window.API && window.API.utils) {
        window.API.utils.mostrarToast(mensagem, 'success');
    } else {
        alert(mensagem);
    }
}

// Validar formulário antes de enviar
function validarFormulario(form) {
    const campos = form.querySelectorAll('[required]');
    for (const campo of campos) {
        if (!campo.value || campo.value.trim() === '') {
            campo.classList.add('border-red-500');
            campo.focus();
            mostrarErro('Preencha todos os campos obrigatórios');
            return false;
        }
        campo.classList.remove('border-red-500');
    }
    return true;
}

// Formatar data para exibição
function formatarDataExibicao(data) {
    if (!data) return '';
    const date = new Date(data);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Formatar hora para exibição
function formatarHoraExibicao(data) {
    if (!data) return '';
    const date = new Date(data);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Exportar utilitários
window.UX = {
    setLoading,
    mostrarErro,
    mostrarSucesso,
    validarFormulario,
    formatarDataExibicao,
    formatarHoraExibicao
};