# Guia de Configuração

## Variáveis de Ambiente

O sistema utiliza um arquivo `.env` para configuração. Copie o `.env.example` e ajuste conforme necessário.

### Configurações do Servidor

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `APP_NAME` | Nome da aplicação | Automated Publishing Agent |
| `APP_VERSION` | Versão da aplicação | 1.0.0 |
| `DEBUG` | Ativa modo debug | True |
| `HOST` | Host do servidor | 0.0.0.0 |
| `PORT` | Porta do servidor | 8000 |
| `RELOAD` | Auto-reload em desenvolvimento | True |

### Configurações de CORS

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `CORS_ORIGINS` | Origens permitidas | * |
| `CORS_CREDENTIALS` | Permitir credenciais | True |
| `CORS_METHODS` | Métodos HTTP permitidos | * |
| `CORS_HEADERS` | Headers permitidos | * |

### Configurações de Banco de Dados

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão | sqlite:///./automated_publishing.db |
| `DB_HOST` | Host do PostgreSQL | localhost |
| `DB_PORT` | Porta do PostgreSQL | 5432 |
| `DB_NAME` | Nome do banco | automated_publishing |
| `DB_USER` | Usuário do banco | usuario |
| `DB_PASSWORD` | Senha do banco | senha |

**Para usar PostgreSQL em produção:**
```bash
DATABASE_URL=postgresql://usuario:senha@localhost:5432/automated_publishing
```

### Configurações de Logging

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `LOG_LEVEL` | Nível de log | INFO |
| `LOG_FORMAT` | Formato do log | %(asctime)s - %(name)s - %(levelname)s - %(message)s |

### Configurações de Mídia

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `ALLOWED_VIDEO_EXTENSIONS` | Extensões permitidas | .mp4,.mov,.avi,.mkv |
| `MAX_VIDEO_SIZE_MB` | Tamanho máximo (MB) | 500 |
| `MAX_UPLOAD_SIZE` | Tamanho máximo (bytes) | 524288000 |

### Configurações de Agendamento

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SCHEDULER_TIMEZONE` | Fuso horário | America/Sao_Paulo |

## Configuração de Plataformas

### YouTube
| Variável | Descrição |
|----------|-----------|
| `YOUTUBE_API_URL` | URL da API de upload |
| `YOUTUBE_API_KEY` | Chave da API do YouTube |
| `YOUTUBE_ACCESS_TOKEN` | Token de acesso OAuth |

### Instagram
| Variável | Descrição |
|----------|-----------|
| `INSTAGRAM_API_URL` | URL da API do Instagram |
| `INSTAGRAM_ACCESS_TOKEN` | Token de acesso |

### TikTok
| Variável | Descrição |
|----------|-----------|
| `TIKTOK_API_URL` | URL da API de upload |
| `TIKTOK_ACCESS_TOKEN` | Token de acesso |

### Facebook
| Variável | Descrição |
|----------|-----------|
| `FACEBOOK_API_URL` | URL da API de upload |
| `FACEBOOK_ACCESS_TOKEN` | Token de acesso |

### Kwai
| Variável | Descrição |
|----------|-----------|
| `KWAI_API_URL` | URL da API de upload |
| `KWAI_ACCESS_TOKEN` | Token de acesso |

## Configuração para Produção

1. **Desative o modo debug:**
   ```bash
   DEBUG=False
   ```

2. **Use PostgreSQL:**
   ```bash
   DATABASE_URL=postgresql://usuario:senha@localhost:5432/automated_publishing
   ```

3. **Configure CORS para produção:**
   ```bash
   CORS_ORIGINS=https://seu-dominio.com
   ```

4. **Use um servidor WSGI/ASGI:**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app
   ```

5. **Configure logging para produção:**
   ```bash
   LOG_LEVEL=WARNING