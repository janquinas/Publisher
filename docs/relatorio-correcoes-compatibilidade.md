# Relatório de Correções de Compatibilidade Backend/Frontend

**Data:** Agosto de 2026  
**Responsável:** Kiro (análise e implementação automática)  
**Escopo:** Identificação e correção das desconexões entre o backend (FastAPI/Python) e o frontend (HTML/JavaScript) do Automated Publishing Agent.

---

## Contexto

O projeto foi desenvolvido por dois desenvolvedores trabalhando em paralelo: um responsável pelo backend (`backend/`, `core/`) e outro pelo frontend (`frontend/`). Após uma análise completa de todos os arquivos — controllers, mappers, modelos Pydantic, arquivos HTML e JavaScript — foram identificadas 8 desconexões entre as duas partes. Todas foram corrigidas nesta sessão.

---

## Correções Aplicadas

### 1. `POST /api/auth/update-photo` — Endpoint não aceitava JSON body

**Arquivo:** `backend/controllers/auth_controller.py`

**Problema:** O endpoint `update-photo` declarava o campo `photo` como parâmetro de query string (`Optional[str] = None`). O frontend (`profile_modal.js`) enviava a requisição com `Content-Type: application/json` e body `{ "photo": "data:image/..." }`. O FastAPI não faz parse automático de JSON body para parâmetros simples, então `photo` chegava sempre como `None` — a foto nunca era salva no banco.

**Correção:** Criada a classe `UpdatePhotoRequest(BaseModel)` com o campo `photo: str` e o endpoint passou a receber esse modelo como body. O token de autenticação continua sendo lido do header `Authorization: Bearer`.

```python
# Antes
async def update_photo(photo: Optional[str] = None, token: Optional[str] = None, ...):

# Depois
class UpdatePhotoRequest(BaseModel):
    photo: str

async def update_photo(request: UpdatePhotoRequest, authorization: Optional[str] = None, ...):
```

---

### 2. Desconexão entre criação e listagem de agendamentos

**Arquivos:** `frontend/posts-agendados.html`, `backend/controllers/publication_controller.py`, `backend/mappers/response_mapper.py`

**Problema:** A página `posts-agendados.html` criava novos agendamentos via `API.Publication.create()` (`POST /api/publications/`), mas listava os dados via `API.Media.list()` (`GET /api/media/`). Editava via `API.Media.update()` e excluía via `API.Media.delete()`. Embora ambos os caminhos gravassem na mesma tabela de banco, os contratos de resposta eram diferentes: `/api/media/` não retorna `platforms` nem `status` de agendamento no mesmo formato que `/api/publications/`. Isso causava inconsistência nos dados exibidos.

**Correção:** A página `posts-agendados.html` foi atualizada para usar exclusivamente `API.Publication.*` em todas as operações:
- Listagem: `API.Publication.list()` → `GET /api/publications/`
- Edição: `API.Publication.update()` → `PUT /api/publications/{id}`
- Exclusão: `API.Publication.delete()` → `DELETE /api/publications/{id}`
- Criação: já usava `API.Publication.create()` — mantido

Também foi ajustado o mapeamento de campos no frontend para ler `platforms[0]` (array retornado pelo endpoint) como a rede social do post.

---

### 3. `PublicationResponse` com campos faltando

**Arquivos:** `backend/controllers/publication_controller.py`, `backend/mappers/response_mapper.py`

**Problema A:** O modelo Pydantic `PublicationResponse` não declarava os campos `updated_at` nem `scheduled_at`. O `ResponseMapper.to_publication_response()` já incluía `updated_at` no dicionário retornado, mas o Pydantic o filtrava silenciosamente por não estar declarado no modelo. O frontend de `posts-agendados.html` precisava de `scheduled_at` para montar a data/hora do agendamento.

**Problema B:** O `ResponseMapper` não extraía `scheduled_at` do objeto `schedule` da publicação.

**Correção:** 
- `PublicationResponse` agora declara `scheduled_at: Optional[datetime] = None` e `updated_at: Optional[datetime] = None`
- `ResponseMapper.to_publication_response()` agora extrai `scheduled_at` do atributo `schedule.scheduled_at` quando disponível

```python
# Modelo atualizado
class PublicationResponse(BaseModel):
    id: str
    title: str
    description: str
    platforms: List[str]
    status: str
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
```

---

### 4. `POST /api/platforms/{name}/connect` — Payload incorreto

**Arquivo:** `frontend/js/api_client.js`

**Problema:** O método `PlatformAPI.connect(name, credentials)` em `api_client.js` passava o objeto de credenciais diretamente como body da requisição. O backend define o modelo `ConnectRequest` com a estrutura `{ "credentials": {} }`. Portanto, ao chamar `API.Platform.connect('instagram', {})`, o body enviado era `{}` em vez de `{ "credentials": {} }`.

**Correção:** O método agora envolve as credenciais no objeto esperado:

```js
// Antes
async connect(name, credentials) { return apiRequest('/platforms/' + name + '/connect', 'POST', credentials); },

// Depois
async connect(name, credentials) { return apiRequest('/platforms/' + name + '/connect', 'POST', { credentials: credentials || {} }); },
```

---

### 5. HTML inválido em `conexoes.html` — Script fora do `</body>`

**Arquivo:** `frontend/conexoes.html`

**Problema:** O bloco `<script>` da página estava posicionado após o fechamento `</body></html>`, tornando o HTML estruturalmente inválido. Além disso, o arquivo tinha um fechamento duplicado de `</body></html>` — um antes do script e um depois. A ausência de `App.init()` no `DOMContentLoaded` desta página também significava que a autenticação não era verificada.

**Correção:**
- O bloco `<script>` foi movido para dentro do `</body>`
- O fechamento duplicado `</body></html>` foi removido
- `App.init()` foi adicionado ao handler `DOMContentLoaded`

---

### 6. `App.init()` duplicado em `index.html`

**Arquivo:** `frontend/index.html`

**Problema:** O arquivo tinha dois listeners `DOMContentLoaded` separados, ambos chamando `App.init()` e as mesmas funções de carregamento. Isso causava dupla inicialização: dois carregamentos do usuário, dois setups de logout, dois setups de modais.

**Correção:** O segundo listener (redundante) foi removido. O primeiro, que já chamava `App.init()`, `carregarPublicacoes()`, `carregarConexoes()` e `carregarMidia()`, foi mantido como único ponto de inicialização.

---

### 7. Dependência HTMX não utilizada em `login.html` e `cadastro.html`

**Arquivos:** `frontend/login.html`, `frontend/cadastro.html`

**Problema:** Ambas as páginas importavam a biblioteca HTMX (`htmx.org@1.9.2`), mas não utilizavam nenhum atributo `hx-*` em seus elementos. O HTMX era um resíduo de uma versão anterior do projeto. Carregar uma biblioteca não utilizada aumenta o tempo de carregamento desnecessariamente.

**Observação:** As páginas `esqueci-senha.html` e `redefinir-senha.html` também importam HTMX, mas elas **utilizam** os atributos `hx-post`, `hx-target` e `hx-swap` — portanto foram mantidas intactas.

**Correção:** A tag `<script src="https://unpkg.com/htmx.org@1.9.2">` foi removida de `login.html` e `cadastro.html`.

---

### 8. Documentação da API desatualizada

**Arquivo:** `docs/technical/api-documentation.md`

**Problema:** O documento estava incompleto e desatualizado em vários pontos:
- Endpoint `/api/auth/me` não documentado
- Endpoints `/api/auth/update-photo`, `/api/auth/request-email-change`, `/api/auth/confirm-email-change` ausentes
- Google OAuth não documentado
- Endpoint `/api/analytics/by-month` ausente
- `/api/analytics/overview` documentado sem os campos `total_media`, `pending_schedules` e `timestamp`
- `PublicationResponse` documentado sem `scheduled_at` e `updated_at`
- Toda a seção `/api/media/` ausente
- Endpoints OAuth de plataformas (`/oauth/start`, `/oauth/callback`) ausentes
- Sem documentação de variáveis de ambiente
- Sem documentação das rotas de frontend servidas pelo backend

**Correção:** O arquivo foi completamente reescrito com todos os endpoints reais, campos corretos, comportamentos de erro, query params, variáveis de ambiente e rotas de frontend.

---

## Resumo dos Arquivos Modificados

| Arquivo | Tipo de alteração |
|---------|-------------------|
| `backend/controllers/auth_controller.py` | Adicionado `UpdatePhotoRequest` BaseModel; endpoint `update-photo` refatorado |
| `backend/controllers/publication_controller.py` | `PublicationResponse` com `scheduled_at` e `updated_at` adicionados |
| `backend/mappers/response_mapper.py` | `to_publication_response` agora extrai e retorna `scheduled_at` e `updated_at` |
| `frontend/js/api_client.js` | `PlatformAPI.connect` envolve credenciais em `{ credentials: {} }` |
| `frontend/posts-agendados.html` | Listagem, edição e exclusão migradas para `API.Publication.*` |
| `frontend/conexoes.html` | Script movido para dentro do body; duplicação de `</body></html>` corrigida; `App.init()` adicionado |
| `frontend/index.html` | Listener `DOMContentLoaded` duplicado removido |
| `frontend/login.html` | Import do HTMX removido |
| `frontend/cadastro.html` | Import do HTMX removido |
| `docs/technical/api-documentation.md` | Totalmente reescrito com contratos reais da API |

---

## Estado Final

Após as correções, o contrato entre backend e frontend está alinhado em todos os pontos identificados:

- ✅ Upload de foto de perfil funciona (JSON body aceito pelo backend)
- ✅ Agendamentos criados aparecem na listagem (mesmo endpoint para criar e listar)
- ✅ Conexão de plataformas envia o payload no formato correto
- ✅ `PublicationResponse` expõe `scheduled_at` e `updated_at`
- ✅ `conexoes.html` é HTML válido com script no lugar correto
- ✅ `index.html` inicializa uma única vez
- ✅ `login.html` e `cadastro.html` sem dependências mortas
- ✅ Documentação da API reflete os contratos reais implementados
