# Guia de Instalação

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar o repositório)

## Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/automated-publishing-agent.git
cd automated-publishing-agent
```

### 2. Criar Ambiente Virtual (Recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```bash
# Configurações mínimas para desenvolvimento
APP_NAME=Automated Publishing Agent
APP_VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./automated_publishing.db
```

### 5. Inicializar o Banco de Dados

```bash
python scripts/init_db.py
```

### 6. Iniciar o Servidor

```bash
# Desenvolvimento (com reload automático)
python -m backend.main

# Ou usando uvicorn diretamente
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Acessar a Aplicação

Abra seu navegador e acesse:
- **Frontend:** http://localhost:8000/
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Verificação da Instalação

Execute os testes para verificar se tudo está funcionando:

```bash
python test_backend.py
python test_unificacao.py
python test_final.py
```

Todos os testes devem passar com ✅.