# Guia para Desenvolvedores

## Estrutura do Projeto

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

## Convenções de Código

### Python
- Use **snake_case** para funções e variáveis
- Use **PascalCase** para classes
- Use **UPPER_SNAKE_CASE** para constantes
- Docstrings em formato Google
- Type hints obrigatórios

```python
def create_publication(title: str, description: str) -> Publication:
    """Cria uma nova publicação.
    
    Args:
        title: Título da publicação
        description: Descrição da publicação
        
    Returns:
        Publication criada
    """
    pass
```

### JavaScript
- Use **camelCase** para funções e variáveis
- Use **PascalCase** para classes
- Comentários claros
- Async/await para chamadas assíncronas

## Como Adicionar uma Nova Plataforma

### 1. Criar o Adapter

```python
# core/adapters/nova_plataforma_adapter.py
from core.adapters.base_adapter import BaseAdapter

class NovaPlataformaAdapter(BaseAdapter):
    def authenticate(self, credentials: dict) -> bool:
        # Implementar autenticação
        pass
    
    def publish(self, media_path: str, caption: str) -> dict:
        # Implementar publicação
        pass
```

### 2. Registrar no Orchestrator

```python
# core/services/orchestrator.py
from core.adapters.nova_plataforma_adapter import NovaPlataformaAdapter

self.adapters["nova_plataforma"] = NovaPlataformaAdapter()
```

### 3. Adicionar ao Banco de Dados

```python
# scripts/init_db.py
platforms = [
    PlatformDB(name="nova_plataforma", enabled=True),
    # ... outras plataformas
]
```

### 4. Adicionar Endpoint de Conexão

```python
# backend/controllers/platform_controller.py
@router.post("/{platform_name}/connect")
async def connect_platform(platform_name: str, ...):
    # Implementar conexão
    pass
```

## Como Adicionar um Novo Endpoint

### 1. Criar o Controller

```python
# backend/controllers/novo_controller.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/novo-endpoint")
async def novo_endpoint():
    return {"message": "Novo endpoint"}
```

### 2. Registrar no main.py

```python
# backend/main.py
from backend.controllers import novo_controller

app.include_router(novo_controller.router, prefix="/api/novo", tags=["Novo"])
```

### 3. Adicionar ao API Client

```javascript
// frontend/js/api_client.js
const NovoAPI = {
    async getNovo() {
        return apiRequest('/novo-endpoint');
    }
};

window.API.Novo = NovoAPI;
```

## Como Adicionar uma Nova Página

### 1. Criar o HTML

```html
<!-- frontend/nova-pagina.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="/assets/js/api_client.js"></script>
</head>
<body>
    <!-- Conteúdo -->
</body>
</html>
```

### 2. Adicionar ao Menu

```html
<!-- Em todas as páginas -->
<a href="nova-pagina.html" class="flex items-center gap-3 px-4 py-3 rounded-xl">
    Nova Página
</a>
```

## Testes

### Executar Todos os Testes

```bash
python test_backend.py
python test_nucleo.py
python test_database.py
python test_unificacao.py
python test_final.py
```

### Adicionar Novo Teste

```python
# test_novo.py
def test_nova_funcionalidade():
    """Testa nova funcionalidade"""
    # Setup
    # Execute
    # Assert
    pass
```

## Fluxo de Desenvolvimento

1. **Planejar** — Definir requisitos
2. **Modelar** — Criar/atualizar modelos
3. **Implementar** — Criar controllers, services, adapters
4. **Testar** — Executar testes
5. **Documentar** — Atualizar documentação
6. **Commit** — Salvar alterações

## Debugging

### Logs
```bash
# Ver logs em tempo real
python -m backend.main  # Logs aparecem no console
```

### Debug no VS Code
```json
// .vscode/launch.json
{
    "name": "Python: Backend",
    "type": "python",
    "request": "launch",
    "module": "backend.main"
}
```

## Dependências

### Adicionar Nova Dependência

```bash
pip install nome_da_dependencia
pip freeze > requirements.txt
```

### Atualizar Dependências

```bash
pip install --upgrade -r requirements.txt