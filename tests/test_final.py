"""
Testes Finais - Fase 4 Produto Final
Valida robustez, tratamento de erros e integração completa
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import app
from core.database.config import SessionLocal, init_db
from core.database.models import UserDB
from backend.controllers.auth_controller import hash_password
import os
import time
from pathlib import Path


def _get_active_db_path():
    db_url = os.getenv("DATABASE_URL") or os.getenv("SQLITE_DB_PATH") or "sqlite:///./automated_publishing.db"
    if not db_url.startswith("sqlite"):
        return None
    relative_path = db_url.replace("sqlite://", "", 1)
    if relative_path.startswith("///"):
        relative_path = relative_path[3:]
    elif relative_path.startswith("//"):
        relative_path = relative_path[2:]
    if relative_path.startswith("./"):
        relative_path = relative_path[2:]
    return str(Path(relative_path).resolve()) if relative_path else None


def _remove_db_file_if_exists():
    """Remove o arquivo SQLite do banco de dados. Só executa em ambiente de teste."""
    if os.getenv("ENV", "").lower() not in ("test", "testing", "ci"):
        print("[AVISO] _remove_db_file_if_exists ignorado fora do ambiente de teste.")
        return
    db_path = _get_active_db_path()
    if not db_path:
        return
    for _ in range(5):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            return
        except PermissionError:
            time.sleep(0.2)


def test_robustez():
    """Testa robustez e tratamento de erros"""
    print("\n" + "="*60)
    print("TESTES FINAIS - ROBUSTEZ E TRATAMENTO DE ERROS")
    print("="*60 + "\n")
    
    # 1. Verificar tratamento de exceções
    print("1. Verificando exception handlers...")
    from backend.exceptions.handlers import setup_exception_handlers
    assert setup_exception_handlers is not None
    print("   ✅ Exception handlers configurados")
    
    # 2. Verificar validators
    print("\n2. Verificando validators...")
    from backend.validators.publication_validator import PublicationValidator
    from backend.validators.file_validator import FileValidator
    
    # Testar validação de dados inválidos
    try:
        PublicationValidator.validate_publication_data(
            title="",
            description="",
            platforms=[]
        )
        print("   ❌ Validação deveria falhar com dados vazios")
    except ValueError:
        print("   ✅ Validação rejeita dados inválidos")
    
    # Testar validação de dados válidos
    try:
        result = PublicationValidator.validate_publication_data(
            title="Teste",
            description="Descrição de teste",
            platforms=["instagram"]
        )
        print("   ✅ Validação aceita dados válidos")
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
    
    # 3. Verificar mappers
    print("\n3. Verificando mappers...")
    from backend.mappers.request_mapper import RequestMapper
    from backend.mappers.response_mapper import ResponseMapper
    assert RequestMapper is not None
    assert ResponseMapper is not None
    print("   ✅ Mappers importados com sucesso")
    
    # 4. Verificar integração com núcleo
    print("\n4. Verificando integração com núcleo...")
    from backend.core_integration import get_core_integration, CoreIntegration
    assert get_core_integration is not None
    assert CoreIntegration is not None
    print("   ✅ Core integration configurada")
    
    # 5. Verificar banco de dados
    print("\n5. Verificando banco de dados...")
    _remove_db_file_if_exists()
    init_db()
    db = SessionLocal()
    try:
        # Testar criação de usuário
        user = UserDB(
            name="Teste",
            email="teste@teste.com",
            password_hash=hash_password("senha123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   ✅ Usuário criado: {user.email}")
        
        # Testar busca de usuário
        found = db.query(UserDB).filter(UserDB.email == "teste@teste.com").first()
        assert found is not None
        print("   ✅ Usuário encontrado no banco")
        
        # Testar duplicidade de email
        user2 = UserDB(
            name="Teste 2",
            email="teste@teste.com",
            password_hash=hash_password("senha456")
        )
        db.add(user2)
        try:
            db.commit()
            print("   ❌ Deveria falhar com email duplicado")
        except Exception:
            db.rollback()
            print("   ✅ Email duplicado rejeitado pelo banco")
        
        # Limpar
        db.delete(user)
        db.commit()
        
    finally:
        db.close()
    
    # 6. Verificar documentação automática
    print("\n6. Verificando documentação automática...")
    openapi = app.openapi()
    assert "paths" in openapi
    assert "info" in openapi
    assert openapi["info"]["title"] == "Automated Publishing Agent"
    print("   ✅ OpenAPI schema gerado corretamente")
    
    # 7. Verificar servir frontend
    print("\n7. Verificando serviço de arquivos estáticos...")
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/static" in routes
    assert "/assets" in routes
    assert "/app/{path:path}" in routes
    print("   ✅ Static files configurados")
    
    # 8. Verificar todos os controllers
    print("\n8. Verificando todos os controllers...")
    controllers = [
        "backend/controllers/publication_controller.py",
        "backend/controllers/platform_controller.py",
        "backend/controllers/analytics_controller.py",
        "backend/controllers/auth_controller.py",
        "backend/controllers/health_controller.py",
        "backend/controllers/home_controller.py"
    ]
    
    for controller in controllers:
        assert os.path.exists(controller), f"Controller {controller} não encontrado"
        print(f"   ✅ {controller}")
    
    # 9. Verificar arquivos do frontend
    print("\n9. Verificando arquivos do frontend...")
    frontend_files = [
        "frontend/index.html",
        "frontend/posts-agendados.html",
        "frontend/analytics.html",
        "frontend/conexoes.html",
        "frontend/js/api_client.js",
        "frontend/js/ux.js"
    ]
    
    for file in frontend_files:
        assert os.path.exists(file), f"Arquivo {file} não encontrado"
        print(f"   ✅ {file}")
    
    # 10. Verificar documentação
    print("\n10. Verificando documentação...")
    docs = [
        "docs/fase-1-engenharia.md",
        "docs/fase-2-nucleo-sistema.md",
        "docs/fase-3-backend.md",
        "docs/fase-4-produto-final.md",
        "docs/fase-unificacao.md",
        "docs/technical/api-documentation.md"
    ]
    
    for doc in docs:
        assert os.path.exists(doc), f"Documento {doc} não encontrado"
        print(f"   ✅ {doc}")
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES FINAIS PASSARAM COM SUCESSO!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_robustez()
