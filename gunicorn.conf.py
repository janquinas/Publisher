"""
Configuração do Gunicorn para produção.

Uso:
    gunicorn -c gunicorn.conf.py backend.main:app
"""
import os

# Bind
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Workers — fixado em 1 para compatibilidade com sessões em memória.
# O sistema é de uso pessoal (single-user), então 1 worker é suficiente.
# Se no futuro migrar sessões para Redis/banco, remova esta linha e o
# cálculo dinâmico voltará a funcionar.
workers = int(os.getenv("GUNICORN_WORKERS", "1"))

# Worker class (ASGI via Uvicorn)
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

# Logging
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "warning")
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")    # stderr
capture_output = True

# Reinício
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Limites
worker_connections = 1000