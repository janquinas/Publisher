"""
Teste de validação do Backend
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import app


def test_backend():
    """Testa a inicialização do backend"""
    print("\n" + "="*60)
    print("TESTE DO BACKEND")
    print("="*60 + "\n")
    
    # Verificar se a aplicação foi criada
    print("1. Verificando aplicação FastAPI...")
    assert app is not None
    print(f"   ✅ Aplicação criada: {app.title}")
    print(f"   ✅ Versão: {app.version}")
    print(f"   ✅ Debug: {app.debug}\n")
    
    # Obter OpenAPI schema
    print("2. Obtendo OpenAPI schema...")
    openapi = app.openapi()
    paths = openapi.get("paths", {})
    
    print(f"   ✅ Total de paths: {len(paths)}")
    for path in paths:
        print(f"   ✅ {path}")
    
    print("\n")
    
    # Verificar documentação automática
    print("3. Verificando documentação automática...")
    assert "/docs" in [r.path for r in app.routes if hasattr(r, "path")]
    assert "/redoc" in [r.path for r in app.routes if hasattr(r, "path")]
    assert "/openapi.json" in [r.path for r in app.routes if hasattr(r, "path")]
    
    print("   ✅ Swagger UI disponível em /docs")
    print("   ✅ ReDoc disponível em /redoc")
    print("   ✅ OpenAPI disponível em /openapi.json\n")
    
    # Verificar controllers
    print("4. Verificando controllers...")
    has_health = "/health" in paths
    has_publications = "/api/publications/" in paths
    
    assert has_health, "Health controller não encontrado"
    assert has_publications, "Publication controller não encontrado"
    
    print("   ✅ Health controller configurado")
    print("   ✅ Publication controller configurado\n")
    
    # Verificar arquivos estáticos
    print("5. Verificando arquivos estáticos...")
    has_static = any("/static" in r.path for r in app.routes if hasattr(r, "path"))
    assert has_static, "Static files não configurado"
    print("   ✅ Static files configurado\n")
    
    print("="*60)
    print("✅ BACKEND VALIDADO COM SUCESSO!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_backend()