# Documentação Técnica da API

## Visão Geral

A API do Automated Publishing Agent é uma API RESTful construída com FastAPI, seguindo os padrões OpenAPI 3.0. Todas as respostas são em formato JSON.

**Base URL:** `http://localhost:8000`  
**Documentação interativa:** `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## Autenticação

A API usa autenticação por token de sessão em memória. Após login ou cadastro, o token retornado deve ser enviado em todas as requisições protegidas via header HTTP:

```
Authorization: Bearer <token>
```

O token também pode ser passado como query string `?token=<token>` nos endpoints de auth (compatibilidade com OAuth redirect).

---

## Endpoints

### Auth — `/api/auth`

#### `POST /api/auth/register`
Cadastra um novo usuário.

**Request Body:**
```json
{
  "name": "string",
  "email": "string (email válido)",
  "password": "string (mínimo 8 caracteres)"
}
```

**Response 201:**
```json
{
  "success": true,
  "token": "string",
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "profile_photo": "string | null"
  }
}
```

**Erros:** `400` — email já cadastrado ou senha muito curta.

---

#### `POST /api/auth/login`
Realiza login e retorna token de sessão.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "success": true,
  "token": "string",
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "profile_photo": "string | null"
  }
}
```

**Erros:** `401` — credenciais inválidas.

---

#### `POST /api/auth/logout`
Finaliza a sessão atual.

**Response 200:**
```json
{
  "success": true,
  "message": "Logout realizado com sucesso"
}
```

---

#### `GET /api/auth/session`
Verifica se o token de sessão é válido.

**Response 200:**
```json
{
  "authenticated": true,
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "profile_photo": "string | null"
  }
}
```

Retorna `{ "authenticated": false }` quando o token está ausente ou inválido (sem lançar 401).

---

#### `GET /api/auth/me`
Retorna os dados do usuário autenticado. Comportamento idêntico ao `/session`.

**Response 200:**
```json
{
  "authenticated": true,
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "profile_photo": "string | null"
  }
}
```

---

#### `POST /api/auth/recuperar-senha`
Solicita link de redefinição de senha por e-mail.

**Request Body:**
```json
{ "email": "string" }
```

**Response 200:**
```json
{
  "success": true,
  "message": "Email de recuperacao enviado",
  "reset_link": "string | null"
}
```

> `reset_link` é retornado apenas em ambiente sem SMTP configurado (desenvolvimento). Em produção, o link é enviado por e-mail e este campo vem `null`.

---

#### `POST /api/auth/redefinir-senha`
Redefine a senha usando o token recebido por e-mail.

**Request Body:**
```json
{
  "token": "string",
  "password": "string (mínimo 8 caracteres)"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Senha redefinida com sucesso"
}
```

**Erros:** `400` — token inválido, expirado ou senha muito curta.

---

#### `POST /api/auth/request-email-change`
Envia link para confirmar alteração de e-mail.

**Request Body:**
```json
{
  "email": "string (email atual)",
  "new_email": "string (novo email)"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Link de alteracao enviado",
  "reset_link": "string | null"
}
```

---

#### `POST /api/auth/confirm-email-change`
Confirma a alteração de e-mail com o token recebido.

**Request Body:**
```json
{
  "token": "string",
  "new_email": "string"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Email atualizado com sucesso",
  "email": "string (novo email)"
}
```

---

#### `POST /api/auth/update-photo`
Persiste a foto de perfil do usuário autenticado como data URL base64.

**Request Body:**
```json
{ "photo": "string (data URL base64, ex: data:image/png;base64,...)" }
```

**Response 200:**
```json
{
  "success": true,
  "profile_photo": "string"
}
```

**Erros:** `401` — não autenticado.

---

#### `GET /api/auth/google`
Redireciona o navegador para o consent screen do Google OAuth.  
Requer `GOOGLE_CLIENT_ID` configurado no `.env`.

#### `GET /api/auth/google/callback`
Callback OAuth do Google. Troca o `code` pelo token e redireciona para o frontend.

- Novo usuário → redireciona para `onboarding.html?token=...&name=...&email=...&photo=...`
- Usuário existente → redireciona para `login.html?token=...&name=...&email=...&photo=...`

---

### Publications — `/api/publications`

Todos os endpoints exigem `Authorization: Bearer <token>`.

#### `POST /api/publications/`
Cria uma nova publicação (com ou sem arquivo de vídeo já existente).

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "platforms": ["instagram", "tiktok", "youtube", "facebook", "kwai"],
  "scheduled_at": "datetime ISO 8601 (opcional)",
  "media_path": "string (opcional — caminho de arquivo já enviado via /api/media/)",
  "media_size_mb": 0.0,
  "media_format": "mp4"
}
```

**Response 201:**
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "platforms": ["string"],
  "status": "pending | scheduled | completed | cancelled",
  "scheduled_at": "datetime ISO 8601 | null",
  "created_at": "datetime ISO 8601",
  "updated_at": "datetime ISO 8601"
}
```

---

#### `GET /api/publications/`
Lista todas as publicações.

**Response 200:**
```json
{
  "publications": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "platforms": ["string"],
      "status": "string",
      "scheduled_at": "datetime ISO 8601 | null",
      "created_at": "datetime ISO 8601",
      "updated_at": "datetime ISO 8601"
    }
  ],
  "total": 0
}
```

---

#### `GET /api/publications/{publication_id}`
Busca uma publicação por ID.

**Response 200:** (mesma estrutura do item acima)

**Erros:** `404` — publicação não encontrada.

---

#### `PUT /api/publications/{publication_id}`
Atualiza título, descrição, plataformas e agendamento de uma publicação.

**Request Body:** (mesmo que `POST /api/publications/`)

**Response 200:** (mesma estrutura de `GET /api/publications/{id}`)

---

#### `DELETE /api/publications/{publication_id}`
Remove uma publicação permanentemente.

**Response 204:** No Content

---

#### `POST /api/publications/{publication_id}/publish`
Executa a publicação imediatamente, ignorando o agendamento.

**Response 200:** (mesma estrutura de `GET /api/publications/{id}`)

---

#### `POST /api/publications/{publication_id}/cancel`
Cancela um agendamento pendente.

**Response 200:**
```json
{
  "success": true,
  "message": "Publicação {id} cancelada com sucesso",
  "timestamp": "datetime ISO 8601"
}
```

---

### Media — `/api/media`

Todos os endpoints exigem `Authorization: Bearer <token>`.

Gerencia o upload e biblioteca de arquivos de vídeo. Internamente, cada vídeo enviado cria um registro em `publications` e opcionalmente um `schedule`.

#### `POST /api/media/`
Faz upload de um arquivo de vídeo e cria a publicação correspondente.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `file` | File | Sim | Arquivo de vídeo (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`) |
| `title` | string | Não | Título (padrão: nome do arquivo) |
| `description` | string | Não | Descrição |
| `platforms` | string (JSON array) | Não | Ex.: `'["instagram","tiktok"]'` |
| `scheduled_at` | string (ISO 8601) | Não | Data/hora de agendamento |

**Response 201:**
```json
{
  "success": true,
  "media": {
    "id": "string",
    "title": "string",
    "description": "string",
    "media_path": "string (nome do arquivo armazenado)",
    "media_size_mb": "string",
    "media_format": "string",
    "duration_seconds": "string | null",
    "scheduled_at": "datetime ISO 8601 | null",
    "status": "scheduled | pending",
    "created_at": "datetime ISO 8601 | null",
    "updated_at": "datetime ISO 8601 | null"
  }
}
```

---

#### `GET /api/media/`
Lista todos os vídeos enviados.

**Response 200:**
```json
{
  "media": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "media_path": "string",
      "media_size_mb": "string",
      "media_format": "string",
      "duration_seconds": "string | null",
      "scheduled_at": "datetime ISO 8601 | null",
      "status": "scheduled | pending",
      "created_at": "datetime ISO 8601",
      "updated_at": "datetime ISO 8601"
    }
  ],
  "total": 0
}
```

---

#### `GET /api/media/{media_id}`
Busca um vídeo por ID.

**Response 200:** (mesma estrutura do item acima, sem o wrapper de lista)

---

#### `PUT /api/media/{media_id}`
Edita título, descrição e agendamento de um vídeo.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Novo título |
| `description` | string | Nova descrição |
| `scheduled_at` | string (ISO 8601) | Nova data/hora (substitui agendamento anterior) |

**Response 200:**
```json
{ "success": true, "message": "Video atualizado com sucesso" }
```

---

#### `DELETE /api/media/{media_id}`
Remove o vídeo e o arquivo do disco.

**Response 204:** No Content

---

#### `GET /api/media/{media_id}/download`
Retorna o arquivo de vídeo para download ou preview.

**Response 200:** `Content-Type: video/mp4` (stream do arquivo)

---

### Platforms — `/api/platforms`

Todos os endpoints exigem `Authorization: Bearer <token>`.

#### `GET /api/platforms/`
Lista todas as plataformas cadastradas no banco.

**Response 200:**
```json
{
  "platforms": [
    {
      "id": "string",
      "name": "instagram | tiktok | youtube | facebook | kwai",
      "enabled": true,
      "connected": true
    }
  ],
  "total": 0
}
```

---

#### `GET /api/platforms/{platform_name}/status`
Obtém o status de conexão de uma plataforma.

**Response 200:**
```json
{
  "name": "string",
  "enabled": true,
  "connected": true,
  "status": "connected | disconnected"
}
```

---

#### `POST /api/platforms/{platform_name}/connect`
Conecta uma plataforma com credenciais manuais (access token direto).  
Para conexão via OAuth, use `GET /api/platforms/{name}/oauth/start`.

**Request Body:**
```json
{
  "credentials": {
    "access_token": "string"
  }
}
```

> O campo `credentials` é opcional. Se omitido, a plataforma é marcada como conectada sem credenciais (útil para testes).

**Response 200:**
```json
{
  "success": true,
  "message": "string",
  "platform": "string",
  "connected": true
}
```

---

#### `POST /api/platforms/{platform_name}/disconnect`
Desconecta uma plataforma (remove credenciais e desabilita).

**Response 200:**
```json
{
  "success": true,
  "message": "string",
  "platform": "string",
  "connected": false
}
```

---

#### `GET /api/platforms/{platform_name}/oauth/start`
Inicia o fluxo OAuth para a plataforma. Redireciona o navegador para a URL de autorização da rede social.

> Requer as variáveis `{PLATFORM}_CLIENT_ID` e `{PLATFORM}_CLIENT_SECRET` configuradas no `.env`.  
> Kwai não suporta OAuth — use `/connect` com token manual.

**Suportadas:** `instagram`, `facebook`, `youtube`, `tiktok`

---

#### `GET /api/platforms/{platform_name}/oauth/callback`
Callback OAuth da plataforma. Troca o `code` pelo `access_token`, salva no banco e redireciona para `conexoes.html`.

- Sucesso → `conexoes.html?oauth_success={platform}`
- Erro → `conexoes.html?oauth_error={mensagem}`

---

### Analytics — `/api/analytics`

Todos os endpoints exigem `Authorization: Bearer <token>`.

#### `GET /api/analytics/overview`
Visão geral das publicações e resultados.

**Response 200:**
```json
{
  "total_publications": 0,
  "total_results": 0,
  "total_media": 0,
  "pending_schedules": 0,
  "successful": 0,
  "failed": 0,
  "success_rate": 0.0,
  "timestamp": "datetime ISO 8601"
}
```

---

#### `GET /api/analytics/by-platform`
Estatísticas agrupadas por plataforma.

**Response 200:**
```json
{
  "platforms": {
    "instagram": {
      "total": 0,
      "successful": 0,
      "failed": 0,
      "success_rate": 0.0
    }
  },
  "total_platforms": 0
}
```

---

#### `GET /api/analytics/by-month?months=6`
Agrupa publicações por mês nos últimos N meses (padrão: 6).

**Query Params:**

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `months` | int | `6` | Número de meses a retornar |

**Response 200:**
```json
{
  "data": [
    {
      "year": 2026,
      "month": 3,
      "month_name": "Mar",
      "count": 12
    }
  ],
  "total_months": 6
}
```

> Os itens são ordenados do mês mais antigo para o mais recente.

---

#### `GET /api/analytics/success-rate`
Taxa de sucesso geral das publicações.

**Response 200:**
```json
{
  "total": 0,
  "successful": 0,
  "failed": 0,
  "success_rate": 0.0
}
```

---

#### `GET /api/analytics/recent-activity?limit=20`
Logs de atividade recente do sistema.

**Query Params:**

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `limit` | int | `20` | Máximo de entradas a retornar |

**Response 200:**
```json
{
  "activity": [
    {
      "id": "string",
      "level": "info | warning | error",
      "message": "string",
      "module": "string",
      "timestamp": "datetime ISO 8601 | null"
    }
  ],
  "total": 0
}
```

---

### Health

#### `GET /health`
Health check básico.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "datetime ISO 8601",
  "version": "1.0.0",
  "service": "Automated Publishing Agent"
}
```

#### `GET /health/detailed`
Health check detalhado com status dos componentes.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "datetime ISO 8601",
  "version": "1.0.0",
  "service": "Automated Publishing Agent",
  "components": {
    "database": "connected",
    "core": "initialized",
    "scheduler": "running"
  }
}
```

---

## Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request (validação falhou) |
| 401 | Unauthorized (token ausente ou inválido) |
| 404 | Not Found |
| 500 | Internal Server Error |
| 502 | Bad Gateway (falha ao consultar API externa, ex: Google) |

---

## Tratamento de Erros

Todas as respostas de erro seguem o padrão do FastAPI:

```json
{
  "detail": "Descrição do erro"
}
```

---

## Frontend — Rotas de Acesso

O backend serve o frontend estático diretamente:

| Rota | Descrição |
|------|-----------|
| `/` | Redireciona para `/app/index.html` |
| `/app/{path}` | Serve arquivos da pasta `frontend/` |
| `/assets/{path}` | Serve assets estáticos do frontend (JS, CSS) |
| `/static/{path}` | Serve arquivos estáticos do backend |

---

## Variáveis de Ambiente Relevantes

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URL do banco (padrão: `sqlite:///./automated_publishing.db`) |
| `FRONTEND_URL` | URL base do frontend para redirects OAuth |
| `EMAIL_RESET_URL` | URL base para links de reset de senha |
| `SMTP_HOST` | Host SMTP (sem configuração, emails são logados no console) |
| `SMTP_PORT` | Porta SMTP (padrão: `587`) |
| `SMTP_USER` | Usuário SMTP |
| `SMTP_PASSWORD` | Senha SMTP |
| `SMTP_FROM` | Remetente dos emails |
| `GOOGLE_CLIENT_ID` | Client ID do Google OAuth |
| `GOOGLE_CLIENT_SECRET` | Client Secret do Google OAuth |
| `GOOGLE_REDIRECT_URI` | URI de callback do Google OAuth |
| `INSTAGRAM_CLIENT_ID` | Client ID do Instagram |
| `INSTAGRAM_CLIENT_SECRET` | Client Secret do Instagram |
| `FACEBOOK_APP_ID` | App ID do Facebook |
| `FACEBOOK_APP_SECRET` | App Secret do Facebook |
| `YOUTUBE_CLIENT_ID` | Client ID do YouTube (Google Cloud) |
| `YOUTUBE_CLIENT_SECRET` | Client Secret do YouTube |
| `TIKTOK_CLIENT_KEY` | Client Key do TikTok |
| `TIKTOK_CLIENT_SECRET` | Client Secret do TikTok |
