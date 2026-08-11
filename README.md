# Automated Publishing Agent

> Plataforma de automação de publicações em redes sociais.

## 📋 Sobre o Projeto

O **Automated Publishing Agent** é uma aplicação web full-stack que permite automatizar publicações em redes sociais. Com ele, você pode:

- Agendar posts para multiplas plataformas simultaneamente
- Gerenciar uma biblioteca de midias (vídeos)
- Conectar contas via OAuth
- Publicar imediatamente ou agendar para data/hora específica
- Acompanhar metricas e status de publicações

## ✨ Funcionalidades

### 🎥 Biblioteca de Midia
- Upload de vídeos (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`)
- Armazenamento local seguro com UUID
- Metadados: título, descricao, tamanho, formato
- Suporte a agendamento direto da biblioteca

### 📅 Agendamento Inteligente
- Agendamento com data e hora personalizadas
- Fuso horario configurável
- Publicacao automatica via **APScheduler**
- Cancelamento de agendamentos pendentes

### 🔗 Integracao com Plataformas
- **Instagram** — Publicacao de vídeos
- **Facebook** — Paginas e perfis business
- **YouTube** — Upload de vídeos com OAuth 2.0
- **TikTok** — Publicacao via Content Posting API
- **Kwai** — Token manual

### 👤 Autenticacao
- Login tradicional com e-mail e senha
- Cadastro de usuarios com validacao
- Login via **Google OAuth 2.0**
- Recuperacao de senha por e-mail (SMTP configuravel)
- Sessoes seguras com tokens

### 📊 Analytics
- Visao geral de publicacoes
- Estatisticas por plataforma
- Taxa de sucesso de publicacoes
- Atividade recente

## 🚀 Inicio Rapido

> **Dica:** Use os scripts na pasta `iniciar/` para facilitar a inicializacao.

### Pre-requisitos

- **Python 3.10+**
- **pip**
- Contas de desenvolvedor nas redes sociais desejadas

### Instalacao

```bash
# 1. Clone o repositorio
git clone https://github.com/seu-usuario/automated-publishing-agent.git
cd automated-publishing-agent

# 2. Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Instale as dependencias
pip install -r requirements.txt

# 4. Configure as variaveis de ambiente
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/macOS
# Preencha o .env com suas credenciais

# 5. Inicialize o banco de dados
python scripts/init_db.py
```

### Execucao

```bash
# Desenvolvimento (com reload automatico)
python -m backend.main

# Producao com Gunicorn
gunicorn -c gunicorn.conf.py backend.main:app
```

**Ou use os scripts de inicializacao:**

```bash
# Windows - Menu interativo
iniciar\Iniciar.bat

# PowerShell
.\iniciar\start.ps1 dev    # Desenvolvimento
.\iniciar\start.ps1 prod   # Producao
.\iniciar\start.ps1 docker # Docker
```

Acesse a aplicacao: http://localhost:8000

## 📚 Documentacao da API

A API conta com documentacao automatica gerada pelo FastAPI:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Principais Endpoints

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| `GET` | `/` | Redireciona para o frontend |
| `GET` | `/health` | Health check |
| `POST` | `/api/auth/register` | Cadastrar usuario |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/logout` | Logout |
| `GET` | `/api/auth/session` | Verificar sessao |
| `GET` | `/api/auth/google` | Login com Google OAuth |
| `POST` | `/api/publications/` | Criar publicacao |
| `GET` | `/api/publications/` | Listar publicacoes |
| `GET` | `/api/publications/{id}` | Buscar publicacao |
| `PUT` | `/api/publications/{id}` | Atualizar publicacao |
| `DELETE` | `/api/publications/{id}` | Excluir publicacao |
| `POST` | `/api/publications/{id}/publish` | Publicar imediatamente |
| `POST` | `/api/publications/{id}/cancel` | Cancelar agendamento |
| `GET` | `/api/platforms/` | Listar plataformas |
| `GET` | `/api/platforms/{name}/oauth/start` | Iniciar OAuth |
| `GET` | `/api/platforms/{name}/oauth/callback` | Callback OAuth |
| `POST` | `/api/platforms/{name}/connect` | Conectar plataforma |
| `POST` | `/api/platforms/{name}/disconnect` | Desconectar plataforma |
| `POST` | `/api/media/` | Upload de video |
| `GET` | `/api/media/` | Listar biblioteca de midia |
| `GET` | `/api/analytics/overview` | Visao geral |
| `GET` | `/api/analytics/by-platform` | Estatisticas por plataforma |

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│         (HTML5 + Tailwind CSS + JavaScript)          │
├─────────────────────────────────────────────────────┤
│                 BACKEND (FastAPI)                     │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Controllers │─▶│   Mappers    │─▶│ Validators │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
│         │                │                           │
│         └────────────────┼───────────────────────────┘ │
│                          ▼                           │
│              ┌──────────────────────┐                │
│              │  Exception Handlers  │                │
│              └──────────────────────┘                │
│                          │                           │
├─────────────────────────────────────────────────────┤
│                   NÚCLEO (Core)                       │
│                                                     │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ PublicationSvc  │  │      Orchestrator        │  │
│  └────────┬────────┘  └──────────┬───────────────┘  │
│           │                      │                   │
│           │    ┌─────────────────▼────────────┐     │
│           │    │    Platform Adapters         │     │
│           │    │ (YouTube, Instagram, TikTok) │     │
│           │    └──────────────────────────────┘     │
│           │                      │                   │
│           ▼                      ▼                   │
│  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │    Scheduler    │  │   Database Integration   │  │
│  │   (APScheduler) │  │   (SQLAlchemy 2.0)       │  │
│  └─────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   BANCO DE DADOS     │
              │  SQLite (dev) /      │
              │  PostgreSQL (prod)   │
              └──────────────────────┘
```

## 🧪 Testes

```bash
# Testes com pytest
pytest tests/ -v

# Teste especifico
pytest tests/test_backend.py -v
pytest tests/test_nucleo.py -v
pytest tests/test_database.py -v
```

## ⚙️ Configuracao

### Variaveis de Ambiente (.env)

O projeto usa variaveis de ambiente para configuracao. Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
copy .env.example .env  # Windows
```

**Categorias principais:**

| Categoria | Variaveis | Descricao |
|-----------|-----------|-----------|
| **Servidor** | `APP_NAME`, `APP_VERSION`, `DEBUG`, `HOST`, `PORT`, `RELOAD` | Configuracao basica do servidor |
| **CORS** | `CORS_ORIGINS`, `CORS_CREDENTIALS`, `CORS_METHODS`, `CORS_HEADERS` | Controle de acesso cross-origin |
| **Banco de Dados** | `DATABASE_URL`, `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Conexao com banco (SQLite/PostgreSQL) |
| **Google OAuth** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Login com Google |
| **Redes Sociais** | `INSTAGRAM_*`, `FACEBOOK_*`, `YOUTUBE_*`, `TIKTOK_*`, `KWAI_*` | Credenciais OAuth por plataforma |
| **SMTP** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Envio de e-mails |
| **Midia** | `ALLOWED_VIDEO_EXTENSIONS`, `MAX_VIDEO_SIZE_MB`, `MAX_UPLOAD_SIZE` | Limites de upload |

> ⚠️ **Nunca compartilhe o arquivo `.env`** — ele contem segredos.
> Use apenas o `.env.example` para documentar as variaveis necessarias.

### Configuracao de Plataformas

Cada plataforma requer credenciais OAuth obtidas em seus respectivos Developer Portals. Consulte o arquivo `docs/guia-api-keys.md` para instrucoes detalhadas.

**Observacoes importantes:**
- Instagram e Facebook compartilham o mesmo app no Meta for Developers
- YouTube usa a mesma conta Google do login, mas requer credenciais OAuth separadas
- Kwai nao possui OAuth publico — use token manual

## 📁 Estrutura do Projeto

```
Automated Publishing Agent/
├── backend/                  # API FastAPI
│   ├── controllers/          # Rotas HTTP
│   │   ├── auth_controller.py
│   │   ├── publication_controller.py
│   │   ├── platform_controller.py
│   │   ├── media_controller.py
│   │   ├── analytics_controller.py
│   │   └── health_controller.py
│   ├── validators/           # Validacao de dados
│   ├── mappers/              # Conversao HTTP ↔ Core
│   ├── exceptions/           # Exception handlers
│   ├── main.py               # Ponto de entrada
│   ├── config.py             # Configuracoes
│   └── core_integration.py   # Ponte com o nucleo
│
├── core/                     # Nucleo do sistema
│   ├── adapters/             # Adapters por plataforma
│   ├── services/             # Logica de negocio
│   ├── database/             # ORM e repositorios
│   │   ├── models/           # Modelos SQLAlchemy
│   │   └── repositories/     # Repositorios de dados
│   └── config.py             # Configuracoes do core
│
├── frontend/                 # Interface web
│   ├── login.html
│   ├── cadastro.html
│   ├── analytics.html
│   ├── conexoes.html
│   ├── posts-agendados.html
│   ├── ajuda.html
│   ├── css/global.css
│   └── js/
│       ├── app.js
│       ├── api_client.js
│       └── ux.js
│
├── scripts/                  # Scripts utilitarios
│   ├── init_db.py            # Inicializa banco de dados
│   └── check_credentials.py  # Valida credenciais OAuth
│
├── tests/                    # Testes automatizados
│   ├── test_backend.py
│   ├── test_nucleo.py
│   ├── test_database.py
│   ├── test_auth_flow.py
│   └── test_final.py
│
├── iniciar/                  # Scripts de inicializacao (Windows)
│   ├── Iniciar.bat           # Menu interativo para iniciar o projeto
│   └── start.ps1             # Script PowerShell com modos dev/prod/docker
│
├── docs/                     # Documentacao adicional
│   ├── guia-api-keys.md      # Guia de configuracao OAuth
│   └── technical/            # Documentacao tecnica
│
├── .env.example              # Template de variaveis (sem segredos)
├── requirements.txt          # Dependencias
├── requirements-prod.txt     # Dependencias de producao
├── gunicorn.conf.py          # Configuracao Gunicorn
├── CHANGELOG.md              # Historico de alteracoes
└── README.md                 # Este arquivo
```

## 🚢 Deploy

### Producao com Gunicorn + Uvicorn Workers

```bash
# Instalar dependencias de producao
pip install -r requirements.txt -r requirements-prod.txt

# Executar com Gunicorn
gunicorn -c gunicorn.conf.py backend.main:app
```

### Variaveis Importantes para Producao

```env
DEBUG=False
RELOAD=False
CORS_ORIGINS=https://seudominio.com
DATABASE_URL=postgresql://user:pass@host:5432/automated_publishing
BASE_URL=https://seudominio.com
FRONTEND_URL=https://seudominio.com/app/login.html
```

### Docker (Exemplo)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install -r requirements.txt -r requirements-prod.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "backend.main:app"]
```

```bash
# Build e execucao
docker build -t automated-publishing-agent .
docker run -p 8000:8000 --env-file .env automated-publishing-agent
```

## 📄 Licenca

Este projeto esta em desenvolvimento ativo.

## 📞 Suporte

- 📝 **Documentacao:** Consulte a pasta `docs/` para guias detalhados
- 🐛 **Issues:** Abra uma issue no repositorio para reportar bugs

---

## 📊 Status do Projeto

**Fase atual:** Fase 4 — Produto Final ✅

### Progresso
- ✅ Estrutura do repositorio organizada
- ✅ API REST completa com FastAPI
- ✅ Frontend funcional com Tailwind CSS
- ✅ Sistema de autenticacao (Google OAuth + login tradicional)
- ✅ Upload e gerenciamento de midia
- ✅ Agendamento com APScheduler
- ✅ Integracao com 5 plataformas
- ✅ Analytics e metricas
- ✅ Testes automatizados
- ✅ Documentacao da API (Swagger/ReDoc)
- ✅ Deploy em producao com Gunicorn
- ✅ Scripts de inicializacao para Windows

---

**Desenvolvido com ❤️ pela equipe da Janqs e do Aatrox**
