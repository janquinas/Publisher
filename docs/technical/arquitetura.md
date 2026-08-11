# Documentação da Arquitetura

## Visão Geral

O Automated Publishing Agent segue uma arquitetura em camadas com separação clara de responsabilidades entre frontend, backend API e núcleo do sistema.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│          (HTML5 + Tailwind CSS + JavaScript)        │
│                                                     │
│  api_client.js → Fetch API                          │
│  ux.js → Utilitários de UX                          │
├─────────────────────────────────────────────────────┤
│                    BACKEND API                      │
│                    (FastAPI)                        │
│                                                     │
│  Controllers → Validators → Mappers                 │
│       ↓                                             │
│  Exception Handlers → Response Mapper               │
│       ↓                                             │
│  Core Integration                                   │
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

## Camadas e Responsabilidades

### Camada 1: Frontend
- **Responsabilidade:** Interface do usuário
- **Tecnologias:** HTML5, Tailwind CSS, JavaScript (Fetch API)
- **Arquivos:** `frontend/*.html`, `frontend/js/*.js`
- **Comunicação:** API REST via Fetch

### Camada 2: Backend API (FastAPI)
- **Responsabilidade:** Expor endpoints HTTP, validar dados, mapear para o núcleo
- **Tecnologias:** FastAPI, Pydantic, Jinja2
- **Componentes:**
  - **Controllers:** Rotas HTTP
  - **Validators:** Validação de entrada
  - **Mappers:** Conversão HTTP ↔ Núcleo
  - **Exception Handlers:** Tratamento de erros
  - **Core Integration:** Ponte com o núcleo

### Camada 3: Núcleo do Sistema
- **Responsabilidade:** Lógica de negócio
- **Componentes:**
  - **PublicationService:** CRUD de publicações
  - **Scheduler:** Agendamento de publicações
  - **Orchestrator:** Coordenação de publicações
  - **Platform Adapters:** Integração com APIs externas
  - **Database Integration:** Acesso a dados
  - **Log Manager:** Registro de logs
  - **Media Manager:** Gerenciamento de mídia
  - **Result Manager:** Resultados de publicações

### Camada 4: Banco de Dados
- **Responsabilidade:** Persistência de dados
- **Tecnologias:** SQLite (dev), PostgreSQL (prod)
- **ORM:** SQLAlchemy 2.0

## Fluxo de Dados

### Criação de Publicação
1. Frontend envia POST `/api/publications/`
2. Controller valida dados (PublicationValidator)
3. RequestMapper converte para modelo do núcleo
4. PublicationService cria a publicação
5. DatabaseIntegration persiste no banco
6. ResponseMapper converte para resposta HTTP
7. Frontend recebe JSON com ID da publicação

### Agendamento e Publicação
1. Scheduler verifica publicações agendadas
2. Orchestrator coordena a publicação
3. Platform Adapters enviam para APIs externas
4. ResultManager registra resultados
5. LogManager registra logs

## Princípios Arquiteturais

1. **Separação de Responsabilidades:** Cada camada tem uma única responsabilidade
2. **Inversão de Dependência:** Backend depende do núcleo, não do contrário
3. **Single Responsibility:** Cada classe/módulo tem uma única razão para mudar
4. **Open/Closed:** Aberto para extensão, fechado para modificação
5. **Dependency Injection:** CoreIntegration injeta dependências

## Padrões de Projeto Utilizados

- **Adapter Pattern:** Platform Adapters
- **Service Pattern:** PublicationService, Scheduler
- **Repository Pattern:** Database repositories
- **Mapper Pattern:** Request/Response mappers
- **Singleton Pattern:** Settings, Database session
- **Factory Pattern:** CoreIntegration factory

## Decisões Técnicas

| Decisão | Justificativa |
|---------|---------------|
| FastAPI | Performance, documentação automática, async |
| SQLAlchemy 2.0 | ORM maduro, suporte a SQLite e PostgreSQL |
| APScheduler | Agendamento robusto e confiável |
| Jinja2 | Templates server-side para páginas HTML |
| Fetch API | Sem dependências, padrão web |
| SQLite (dev) | Simples, sem configuração |
| PostgreSQL (prod) | Robustez, concorrência |
| Session Auth | Simples, seguro para este escopo |
| SHA256 (hash) | Simples, suficiente para desenvolvimento |