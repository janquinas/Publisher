# Automated Publishing Agent

## 📋 Visão Geral

O **Automated Publishing Agent** é uma plataforma de automação de publicações em redes sociais que permite agendar, gerenciar e publicar conteúdo em múltiplas plataformas (YouTube, Instagram, TikTok, Facebook, Kwai) a partir de uma única interface.

### Funcionalidades Principais
- 📅 **Agendamento de publicações** — Agende posts para data e hora específicas
- 🚀 **Publicação automática** — Conteúdo publicado automaticamente na data marcada
- 📊 **Analytics integrado** — Acompanhe métricas de desempenho por plataforma
- 🔗 **Gestão de conexões** — Conecte e desconecte redes sociais
- 👤 **Autenticação de usuários** — Sistema completo de login e gerenciamento de conta
- 🔄 **CRUD completo** — Crie, leia, atualize e exclua publicações
- ⚠️ **Tratamento de erros robusto** — Mensagens claras e estados de loading

### Tecnologias Utilizadas
- **Backend:** Python + FastAPI
- **Frontend:** HTML5 + Tailwind CSS + JavaScript (Fetch API)
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Agendamento:** APScheduler
- **ORM:** SQLAlchemy 2.0
- **Validação:** Pydantic
- **Documentação API:** OpenAPI 3.0 (Swagger UI + ReDoc)

---

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.10+
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/automated-publishing-agent.git
cd automated-publishing-agent

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 4. Inicialize o banco de dados
python scripts/init_db.py

# 5. Inicie o servidor
python -m backend.main
```

### Execução

```bash
# Desenvolvimento (com reload automático)
python -m backend.main

# Produção
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Acesse: http://localhost:8000

---

## 📚 Documentação da API

### Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Redireciona para o frontend |
| GET | `/health` | Health check |
| GET | `/health/detailed` | Health check detalhado |
| POST | `/api/auth/register` | Cadastrar usuário |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/session` | Verificar sessão |
| POST | `/api/publications/` | Criar publicação |
| GET | `/api/publications/` | Listar publicações |
| GET | `/api/publications/{id}` | Buscar publicação |
| PUT | `/api/publications/{id}` | Atualizar publicação |
| DELETE | `/api/publications/{id}` | Excluir publicação |
| POST | `/api/publications/{id}/publish` | Publicar imediatamente |
| POST | `/api/publications/{id}/cancel` | Cancelar agendamento |
| GET | `/api/platforms/` | Listar plataformas |
| GET | `/api/platforms/{name}/status` | Status da plataforma |
| POST | `/api/platforms/{name}/connect` | Conectar plataforma |
| POST | `/api/platforms/{name}/disconnect` | Desconectar plataforma |
| GET | `/api/analytics/overview` | Visão geral |
| GET | `/api/analytics/by-platform` | Estatísticas por plataforma |
| GET | `/api/analytics/success-rate` | Taxa de sucesso |
| GET | `/api/analytics/recent-activity` | Atividade recente |

### Documentação Automática
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Exemplos de Uso

#### Registrar usuário
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "João Silva", "email": "joao@example.com", "password": "senha123"}'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "joao@example.com", "password": "senha123"}'
```

#### Criar publicação
```bash
curl -X POST http://localhost:8000/api/publications/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Reel — Bastidores do lançamento",
    "description": "Confira os bastidores do nosso lançamento",
    "platforms": ["instagram"],
    "scheduled_at": "2024-12-25T18:00:00"
  }'
```

#### Listar publicações
```bash
curl http://localhost:8000/api/publications/
```

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│          (HTML + Tailwind + JavaScript)             │
│                                                     │
│  Fetch API → api_client.js                          │
├─────────────────────────────────────────────────────┤
│                    BACKEND API                      │
│                    (FastAPI)                        │
│                                                     │
│  Controllers → Validators → Mappers                 │
│       ↓                                             │
│  Exception Handlers → Response Mapper               │
├─────────────────────────────────────────────────────┤
│                    NÚCLEO                           │
│              (Core do Sistema)                      │
│                                                     │
│  PublicationService → Orchestrator → Adapters       │
│       ↓                                             │
│  Scheduler → DatabaseIntegration                    │
├─────────────────────────────────────────────────────┤
│                 BANCO DE DADOS                      │
│                (SQLite/PostgreSQL)                  │
└─────────────────────────────────────────────────────┘
```

### Componentes Principais

| Componente | Descrição |
|------------|-----------|
| **Controllers** | Rotas HTTP (FastAPI) |
| **Validators** | Validação de dados de entrada |
| **Mappers** | Conversão entre HTTP e modelos do núcleo |
| **Exception Handlers** | Tratamento centralizado de erros |
| **Core Integration** | Ponte entre backend e núcleo |
| **Publication Service** | Lógica de negócio de publicações |
| **Scheduler** | Agendamento de publicações |
| **Orchestrator** | Coordenação de publicações |
| **Platform Adapters** | Integração com APIs das redes sociais |
| **Database Integration** | Acesso a dados |

---

## 🧪 Testes

```bash
# Testes do backend
python test_backend.py

# Testes do núcleo
python test_nucleo.py

# Testes do banco de dados
python test_database.py

# Testes de integração completa
python test_unificacao.py
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `APP_NAME` | Nome da aplicação | Automated Publishing Agent |
| `APP_VERSION` | Versão | 1.0.0 |
| `DEBUG` | Modo debug | True |
| `HOST` | Host do servidor | 0.0.0.0 |
| `PORT` | Porta do servidor | 8000 |
| `DATABASE_URL` | URL do banco de dados | sqlite:///./automated_publishing.db |
| `LOG_LEVEL` | Nível de log | INFO |

### Configuração de Plataformas

Configure as credenciais de cada plataforma no arquivo `.env`:
- YouTube: `YOUTUBE_API_KEY`, `YOUTUBE_ACCESS_TOKEN`
- Instagram: `INSTAGRAM_ACCESS_TOKEN`
- TikTok: `TIKTOK_ACCESS_TOKEN`
- Facebook: `FACEBOOK_ACCESS_TOKEN`
- Kwai: `KWAI_ACCESS_TOKEN`

---

## 📁 Estrutura do Projeto

```
Automated Publishing Agent/
├── backend/          # API FastAPI
├── core/             # Núcleo do sistema
├── frontend/         # Interface web
├── docs/             # Documentação
├── scripts/          # Scripts utilitários
├── .env.example      # Template de variáveis
├── requirements.txt  # Dependências
└── README.md         # Este arquivo
```

---

## 🚢 Deploy

### Produção com Uvicorn

```bash
# Instalar dependências de produção
pip install gunicorn

# Executar com múltiplos workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app
```

### Docker (futuro)

```bash
docker build -t automated-publishing-agent .
docker run -p 8000:8000 automated-publishing-agent
```

---

## 📄 Licença

Este projeto está sob desenvolvimento para uso interno.

---

## 📞 Suporte

- **Discord:** [Link do Discord]
- **E-mail:** suporte@automatedpublishing.com

---

**Status:** ✅ Em desenvolvimento — Fase 4 (Produto Final) concluída