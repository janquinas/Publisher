# Guia de Deploy

## Preparação para Produção

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar para produção
DEBUG=False
HOST=0.0.0.0
PORT=8000
DATABASE_URL=postgresql://usuario:senha@localhost:5432/automated_publishing
CORS_ORIGINS=https://seu-dominio.com
LOG_LEVEL=WARNING
```

### 2. Instalar Dependências de Produção

```bash
pip install -r requirements.txt
```

### 3. Inicializar Banco de Dados

```bash
python scripts/init_db.py
```

## Deploy com Gunicorn + Uvicorn

### Instalação

```bash
pip install gunicorn
```

### Execução

```bash
# 4 workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000

# Com configuração de timeout
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level warning
```

### Configuração Avançada

Crie um arquivo `gunicorn.conf.py`:

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
loglevel = "warning"
accesslog = "/var/log/automated-publishing/access.log"
errorlog = "/var/log/automated-publishing/error.log"
capture_output = True
```

## Deploy com Docker (Recomendado)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:senha@db:5432/automated_publishing
      - DEBUG=False
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: automated_publishing
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: senha
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Execução

```bash
docker-compose up -d
```

## Deploy com Nginx (Reverse Proxy)

### Configuração do Nginx

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /app/backend/static;
    }

    location /assets {
        alias /app/frontend;
    }
}
```

## Monitoramento

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Ver logs em tempo real
tail -f /var/log/automated-publishing/error.log

# Ver logs de acesso
tail -f /var/log/automated-publishing/access.log
```

## Backup do Banco de Dados

### SQLite

```bash
cp automated_publishing.db automated_publishing.db.backup.$(date +%Y%m%d)
```

### PostgreSQL

```bash
pg_dump -U postgres automated_publishing > backup_$(date +%Y%m%d).sql
```

## Segurança

- ✅ Use HTTPS em produção
- ✅ Configure CORS para domínios específicos
- ✅ Use variáveis de ambiente para credenciais
- ✅ Mantenha dependências atualizadas
- ✅ Configure firewall para porta 8000
- ✅ Use usuário não-root para execução