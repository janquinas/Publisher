# Guia de Configuração das API Keys das Redes Sociais

Este guia mostra **exatamente onde obter** cada credencial e **em qual variável do `.env`** colocá-la.

> ⚠️ O arquivo `.env` contém segredos e **nunca deve ser commitado** (já está no `.gitignore`).
> Depois de preencher, valide com: `python scripts/check_credentials.py`

---

## Como o sistema usa as credenciais

Existem **dois níveis** de credenciais:

| Nível | O que é | Onde fica | Quem preenche |
|-------|---------|-----------|---------------|
| **App-level** (Client ID / Client Secret) | Identifica o *seu aplicativo* perante a rede social | `.env` | Você, uma vez |
| **User-level** (Access Token) | Autoriza o *usuário final* a publicar | Banco de dados (tabela `platforms.credentials`) | Gerado automaticamente pelo fluxo OAuth |

Fluxo implementado em `backend/controllers/platform_controller.py`:

```
GET /api/platforms/{plataforma}/oauth/start     → redireciona para a rede social
GET /api/platforms/{plataforma}/oauth/callback  → troca o "code" por access_token e salva no banco
```

A tela `frontend/conexoes.html` é a interface que dispara esse fluxo.

---

## 1. Google (login do próprio app)

Usado para "Entrar com Google" na tela de login.

1. Acesse https://console.cloud.google.com/
2. Crie um projeto (ou selecione um existente).
3. Vá em **APIs e Serviços → Tela de permissão OAuth** e configure (tipo: *Externo*).
4. Vá em **APIs e Serviços → Credenciais → Criar credenciais → ID do cliente OAuth**.
5. Tipo de aplicativo: **Aplicativo da Web**.
6. Em **URIs de redirecionamento autorizados**, adicione:
   ```
   http://localhost:8000/api/auth/google/callback
   ```
7. Copie o **Client ID** e o **Client Secret**.

```env
GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

---

## 2. YouTube (YouTube Data API v3)

1. No mesmo projeto do Google Cloud, vá em **APIs e Serviços → Biblioteca**.
2. Busque e **ative** a `YouTube Data API v3`.
3. Em **Credenciais**, crie um **novo ID do cliente OAuth** (Aplicativo da Web) separado para o YouTube.
4. Escopo necessário: `https://www.googleapis.com/auth/youtube.upload` (já configurado no código).
5. URI de redirecionamento autorizado:
   ```
   http://localhost:8000/api/platforms/youtube/oauth/callback
   ```

```env
YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-...
YOUTUBE_REDIRECT_URI=http://localhost:8000/api/platforms/youtube/oauth/callback
```

> 💡 Enquanto o app estiver em modo "Teste", adicione sua conta em **Usuários de teste**.
> Uploads via API em projetos não verificados ficam com visibilidade *privada* por padrão.

---

## 3. Facebook

1. Acesse https://developers.facebook.com/apps → **Criar aplicativo**.
2. Caso de uso: **Outro** → Tipo: **Negócios**.
3. No painel, vá em **Configurações do app → Básico**:
   - **ID do aplicativo** → `FACEBOOK_APP_ID`
   - **Chave secreta do aplicativo** (clique em *Mostrar*) → `FACEBOOK_APP_SECRET`
4. Adicione o produto **Login do Facebook → Configurações** e inclua em *URIs de redirecionamento do OAuth válidos*:
   ```
   http://localhost:8000/api/platforms/facebook/oauth/callback
   ```
5. Permissões usadas pelo código: `pages_manage_posts`, `pages_read_engagement`
   (precisam de **App Review** para funcionar fora do modo de desenvolvimento).

```env
FACEBOOK_APP_ID=1234567890123456
FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/platforms/facebook/oauth/callback
```

---

## 4. Instagram

O Instagram usa a mesma plataforma Meta.

1. No mesmo app do Facebook (ou um novo), adicione o produto **Instagram**.
2. Para **publicar** conteúdo você precisa da **Instagram Graph API** com:
   - Uma conta Instagram **Profissional/Criador**
   - Vinculada a uma **Página do Facebook**
3. Copie o Client ID / Client Secret do Instagram (ou reutilize o App ID/Secret do Facebook).
4. URI de redirecionamento (OAuth):
   ```
   http://localhost:8000/api/platforms/instagram/oauth/callback
   ```

```env
INSTAGRAM_CLIENT_ID=...
INSTAGRAM_CLIENT_SECRET=...
INSTAGRAM_REDIRECT_URI=http://localhost:8000/api/platforms/instagram/oauth/callback
```

> ⚠️ **Instagram Basic Display** (escopos `user_profile,user_media`, que estão no código hoje)
> permite apenas **leitura**. Para publicar de fato, é necessário migrar para a
> **Instagram Graph API** com escopos como `instagram_content_publish`.

---

## 5. TikTok

1. Acesse https://developers.tiktok.com/ e faça login.
2. **Manage apps → Create an app**.
3. Adicione os produtos **Login Kit** e **Content Posting API**.
4. Em **Credentials**, copie:
   - **Client key** → `TIKTOK_CLIENT_KEY`
   - **Client secret** → `TIKTOK_CLIENT_SECRET`
5. Em **Login Kit → Redirect URI**, adicione:
   ```
   http://localhost:8000/api/platforms/tiktok/oauth/callback
   ```
6. Escopos usados: `user.info.basic`, `video.upload`

```env
TIKTOK_CLIENT_KEY=awxxxxxxxxxxxxxxxx
TIKTOK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TIKTOK_REDIRECT_URI=http://localhost:8000/api/platforms/tiktok/oauth/callback
```

> ⚠️ O TikTok exige domínio **verificado** e HTTPS para produção. Em desenvolvimento,
> use uma URL de túnel (ex.: `ngrok`) se o `localhost` não for aceito.

---

## 6. Kwai

O Kwai **não possui OAuth público**. O código já trata isso: `auth_url` e `token_url` vazios.

Para conectar, use o endpoint de credenciais manuais:

```http
POST /api/platforms/kwai/connect
Content-Type: application/json

{ "credentials": { "access_token": "SEU_TOKEN_KWAI" } }
```

Se você conseguir acesso ao programa de parceiros, preencha:

```env
KWAI_CLIENT_ID=
KWAI_CLIENT_SECRET=
KWAI_REDIRECT_URI=http://localhost:8000/api/platforms/kwai/oauth/callback
```

---

## Resumo das variáveis

| Plataforma | Variáveis obrigatórias | Portal |
|------------|------------------------|--------|
| Google (login) | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | console.cloud.google.com |
| YouTube | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` | console.cloud.google.com |
| Facebook | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | developers.facebook.com |
| Instagram | `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET` | developers.facebook.com |
| TikTok | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | developers.tiktok.com |
| Kwai | (token manual) | — |

---

## Testando a configuração

```bash
# 1. Verificar quais credenciais estão preenchidas
python scripts/check_credentials.py

# 2. Inicializar o banco (se ainda não fez)
python scripts/init_db.py

# 3. Subir o servidor
python -m uvicorn backend.main:app --reload

# 4. Abrir a tela de conexões e clicar em "Conectar" na plataforma desejada
#    http://localhost:8000/app/conexoes.html
```

Erros comuns:

| Erro | Causa |
|------|-------|
| `Credenciais OAuth de X nao configuradas` | `X_CLIENT_ID` vazio no `.env` |
| `?oauth_error=redirect_uri_mismatch` | O redirect URI no portal ≠ o do `.env` |
| `?oauth_error=invalid_state` | Sessão expirou; faça login novamente |
| `OAuth nao disponivel para kwai` | Esperado — use `/connect` com token manual |

---

## Observação importante sobre publicação real

Hoje os adapters em `core/adapters/*.py` estão em **modo simulação** — eles validam o
`access_token` e retornam uma URL fictícia (ex.: `https://www.instagram.com/p/simulated_post_id/`),
sem chamar a API real.

Ou seja: configurar as API keys habilita o **fluxo de conexão/OAuth completo**, mas o
**upload real** ainda precisa ser implementado dentro de cada método `publish()`.
Isso é o próximo passo natural depois de obter as credenciais.
