FROM python:3.12-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependências de produção
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copiar código
COPY . .

# Criar diretório para uploads
RUN mkdir -p backend/static/uploads

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "backend.main:app"]