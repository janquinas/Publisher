# CHANGELOG — Automated Publishing Agent

Todas as alterações registradas por sessão de desenvolvimento.

---

## [Sem versão] — Sessão de correções e melhorias

### Backend

#### `core/database/models/publication.py`
- Adicionada coluna `platforms TEXT` (JSON, ex: `["instagram","tiktok"]`) para persistir as plataformas associadas a cada publicação.
- Adicionada coluna `is_media_only BOOLEAN NOT NULL DEFAULT 0` para distinguir uploads da biblioteca de mídia (`True`) de publicações agendadas criadas pelo usuário (`False`).
- Import `ForeignKey` removido (não usado no modelo); adicionado `Boolean`.

#### `core/database/config.py`
- `init_db()` agora executa migrações manuais via `ALTER TABLE` para adicionar as colunas `platforms` e `is_media_only` em bancos SQLite existentes (idempotente — não quebra em execuções repetidas).
- Suporte equivalente para PostgreSQL via `information_schema`.

#### `core/database/repositories/publication_repository.py`
- `create()` aceita dois novos parâmetros: `platforms: Optional[str]` e `is_media_only: bool = False`.
- `get_all()` agora filtra `is_media_only = False` — retorna apenas publicações agendadas.
- Adicionado método `get_all_media()` que filtra `is_media_only = True` — retorna apenas uploads da biblioteca.
- Arquivo reescrito de forma limpa para corrigir fragmentação acidental gerada durante edições anteriores.

#### `core/services/publication_service.py`
- `create_publication()` persiste a lista de plataformas como JSON na coluna `platforms`.
- `create_publication()` passa `is_media_only=False` ao criar publicações agendadas.
- `_db_to_publication()` agora lê a coluna `platforms` do banco (JSON) e reconstrói objetos `Platform` — antes sempre retornava lista vazia.
- `update_publication()` persiste plataformas ao atualizar.

#### `backend/mappers/response_mapper.py`
- `to_publication_response()` reescrito para ler plataformas tanto da coluna DB (string JSON) quanto de lista Pydantic em memória.
- Lê o relacionamento `schedules` diretamente do objeto SQLAlchemy quando `schedule` Pydantic não estiver disponível.

#### `backend/controllers/media_controller.py`
- `upload_media()` (POST `/api/media/`) agora define `is_media_only=True` ao criar a entrada no banco.
- `list_media()` (GET `/api/media/`) usa `get_all_media()` — lista apenas vídeos da biblioteca, sem misturar com publicações agendadas.
- Simplificado o loop de iteração de schedules usando `next(iter(...), None)`.

#### `backend/controllers/publication_controller.py`
- GET `/api/publications/` chama `publication_service.list_publications()` que agora filtra `is_media_only=False` — publicações recentes e agendamentos não mostram mais uploads de mídia avulsos.

#### `backend/controllers/auth_controller.py`
- Callback Google OAuth (`GET /api/auth/google/callback`) agora inclui o campo `id` do usuário nos parâmetros de redirect (`?token=...&id=...&name=...&email=...&photo=...`).
- Usuários existentes têm `name` e `profile_photo` atualizados a cada login com Google (antes só novos usuários recebiam foto).

#### `backend/controllers/platform_controller.py`
- `oauth_start` (GET `/api/platforms/{name}/oauth/start`) não retorna mais HTTP 500 ou 401 bruto.
  - Sessão inválida/expirada → redireciona para `login.html`.
  - Credenciais não configuradas no `.env` → redireciona para `conexoes.html?oauth_error=<mensagem clara>` com instrução do nome exato da variável de ambiente necessária.
- Corrigido nome da variável de ambiente para TikTok (`TIKTOK_CLIENT_KEY`) e Facebook (`FACEBOOK_APP_ID`) no erro de configuração.

---

### Frontend

#### `frontend/js/app.js`
- `loadUser()` agora faz fallback para dados do `localStorage` quando a sessão expirou no servidor (reinício do processo) — evita redirecionamento indevido ao login por perda de sessão em memória.
- `consumeGoogleToken()` já mapeava `photo → profile_photo` corretamente; confirmado sem alteração necessária.

#### `frontend/js/api_client.js`
- Sem alterações funcionais — `apiRequest()` já enviava `Authorization: Bearer <token>` corretamente em todas as requisições.

#### `frontend/js/i18n.js` *(REMOVIDO)*
- Arquivo deletado. Sistema de tradução foi removido por falta de funcionalidade real.

#### `frontend/index.html` (Dashboard)
- Removida tag `<script src="/assets/js/i18n.js">`.
- Bloco de checkboxes de seleção de redes sociais removido do formulário de upload de vídeo.
- `carregarMidia()` corrigida — estava com o corpo da função solto fora de qualquer declaração; agora é `async function carregarMidia()` válida.
- `carregarPublicacoes()` corrigida para tratar `pub.platforms` de forma segura (verifica se é array antes de chamar `.join()`).
- Modal "Configurações" alterado de `<form method="dialog">` para `<div>` + `<button type="button" onclick="salvarConfiguracoes()">`.
- `salvarConfiguracoes()` implementada: persiste preferências no `localStorage` e exibe toast de confirmação.
- `carregarConfiguracoes()` implementada: carrega preferências salvas ao abrir o modal.
- Seletor de idioma removido do modal de Configurações.

#### `frontend/posts-agendados.html`
- Adicionado `<script src="/assets/js/i18n.js">` → posteriormente removido.
- Modal "Novo Agendamento" convertido de `<form method="dialog" onsubmit="...">` para `<div>` + `<button type="button" onclick="criarNovoPost()">` — corrigido bug onde o modal fechava imediatamente sem executar o handler.
- Modal "Editar Agendamento" recebeu a mesma correção (`salvarEdicao()`).
- `criarNovoPost()` e `salvarEdicao()` tiveram o parâmetro `event` e o `event.preventDefault()` removidos (não mais necessários).
- `criarNovoPost()` corrigido: agora lê `data-media-path` do `<option>` selecionado e envia o nome real do arquivo no disco, em vez do UUID da entrada no banco.
- `carregarMidiaNoSeletor()` agora armazena `data-media-path` (nome do arquivo) em cada `<option>` além de `data-titulo`.
- `abrirModalNovo()` envolve `carregarMidiaNoSeletor()` em try/catch — falha de API não impede mais a abertura do modal.
- `DOMContentLoaded` convertido de `async/await em série` para chamadas independentes com `.catch()` — erro em `carregarConexoes()` não bloqueia mais `carregarAgendamentos()` nem torna o botão inoperante.
- Adicionados `carregarConexoes()` e `carregarConfiguracoes()` com lógica real de API de plataformas para alimentar o aviso de "rede não conectada" no modal.
- Seletor de idioma removido do modal de Configurações.
- `salvarConfiguracoes()` implementada (sem i18n).

#### `frontend/analytics.html`
- Adicionada seção "Desempenho dos posts" com tabela que lista todas as publicações agendadas (título, plataforma, data de agendamento, status) via `GET /api/publications/`.
- `carregarDesempenhoPosts()` implementada.
- Modal "Configurações" corrigido (mesmo padrão de `<div>` + `salvarConfiguracoes()`).
- Seletor de idioma removido.
- Adicionados `carregarConfiguracoes()` e `salvarConfiguracoes()`.
- Tag `<script src="/assets/js/i18n.js">` removida.

#### `frontend/conexoes.html`
- Linhas de Instagram e TikTok eram hardcoded como "Conectado" sem IDs dinâmicos — reescritas com `id="badge-instagram"`, `id="btn-instagram"`, `id="desc-instagram"` (e equivalentes TikTok) para que `renderizarPlataforma()` funcione nos 5 cards.
- `alternarConexao()` substituída por `renderizarPlataforma()` com lógica separada:
  - Plataformas com OAuth (`instagram`, `tiktok`, `youtube`, `facebook`): botão "Conectar" redireciona para `/api/platforms/{nome}/oauth/start?token=<session_token>`.
  - Kwai: sem OAuth público — botão abre modal `modal-kwai` para inserção de access token manual.
- Adicionado modal `modal-kwai` com campo de texto para o token e botão `conectarKwai()`.
- `verificarOAuthCallback()` melhorada:
  - Sucesso: exibe toast com nome da plataforma.
  - Erro de credenciais não configuradas: exibe banner amarelo com instruções de configuração do `.env`.
  - Outros erros: exibe toast de erro.
- `mostrarBannerSetup()` adicionada — renderiza aviso amarelo com o nome da variável de ambiente necessária.
- Modais de confirmação de desconexão de Instagram e TikTok removidos (a lógica passou para `desconectar()`).
- Modal "Configurações" corrigido (sem idioma, com `salvarConfiguracoes()`).
- Tag `<script src="/assets/js/i18n.js">` removida.

#### `frontend/ajuda.html`
- Resposta da pergunta "Onde vejo o desempenho dos meus posts?" atualizada para refletir o que a aba Analytics realmente mostra: gráfico de 6 meses, desempenho por rede, tabela de posts, atividade recente.
- Modal "Configurações" corrigido (sem idioma, com `salvarConfiguracoes()`).
- Tag `<script src="/assets/js/i18n.js">` removida.
- `carregarConfiguracoes()` e `salvarConfiguracoes()` adicionadas ao script da página.

---

### Resumo por área de impacto

| Área | Problema original | Solução |
|---|---|---|
| Biblioteca de mídia | Vídeos uploadados não apareciam; mesma tabela misturava uploads e agendamentos | Coluna `is_media_only`; endpoints separados por tipo |
| Publicações/Agendamentos | Exibiam uploads de mídia junto com posts reais | `get_all()` filtrado por `is_media_only=False` |
| Plataformas na resposta | `platforms: []` sempre vazio ao listar publicações | Persistência em coluna JSON + leitura no mapper |
| Botão "Novo Agendamento" | Modal fechava imediatamente ou não abria | Remoção de `form[method=dialog]`; DOMContentLoaded não-bloqueante |
| Aba Conexões | Botão "Conectar" chamava API com credenciais vazias | Redirecionamento OAuth real + banner de setup |
| Google OAuth | Nome e foto não apareciam no header; usuários existentes sem foto | `id` incluído no redirect; update de nome/foto a cada login |
| Configurações | Botão "Salvar" fechava modal sem fazer nada | `salvarConfiguracoes()` com persistência em `localStorage` |
| Seletor de idioma | Presente mas completamente não-funcional | Removido de todas as páginas; `i18n.js` deletado |
| Analytics | Seção "Desempenho de posts" mencionada na Ajuda mas inexistente | Tabela real implementada com dados do backend |
| Erros OAuth | HTTP 500 bruto quando `.env` não configurado | Redirecionamento com mensagem legível + banner de instrução |

---

## [1.0.1] — Sessão de auditoria e limpeza

### Backend

#### `backend/config.py`
- Fallback de `cors_origins_list` agora retorna `http://localhost:8000` quando `CORS_ORIGINS` está vazio (antes poderia retornar lista vazia).
- Adicionado aviso mais descritivo quando `CORS_ORIGINS='*'` é usado com `CORS_CREDENTIALS=True`.

#### `.env.example`
- Altereado valor padrão de `CORS_ORIGINS` de `*` para `http://localhost:8000` com orientação clara de substituição em produção.

### Frontend

#### `frontend/css/global.css`
- Bloco `@theme` com a paleta de cores completa adicionado a este arquivo central.

#### HTMLs (`index.html`, `login.html`, `cadastro.html`, `analytics.html`, `posts-agendados.html`, `conexoes.html`, `ajuda.html`, `esqueci-senha.html`, `redefinir-senha.html`, `redefinir-email.html`, `onboarding.html`)
- Removidos 11 blocos `@theme` inline duplicados. A paleta agora é carregada via `<link rel="stylesheet" href="/assets/css/global.css">` já presente nos `<head>`.
- Removido código JavaScript inline duplicado de fechamento de modals/dropdowns (`dialog.addEventListener('click', ...)` e `details[open]`). Essa lógica já estava centralizada em `frontend/js/app.js`.

### Repositório / Estrutura

#### Removidos / excluídos do versionamento
- `.env` — removido do repositório por conter credenciais reais.
- `automated_publishing.db` — removido do repositório por ser banco de dados local/sqlite.
- `Publisher/` — removido (pasta vazia sem funcionalidade).
- `venv/` — removido (ambiente virtual, já excluído pelo `.gitignore`).

#### Código morto confirmado
- `backend/controllers/home_controller.py` — router vazio sem endpoints. Mantido fisicamente no disco por ser importado em `backend/main.py`, mas sem efeito funcional.
