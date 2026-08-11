"""
Teste de integração do banco de dados
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from core.database.config import SessionLocal, init_db
from core.database.repositories import (
    PublicationRepository,
    ScheduleRepository,
    ResultRepository,
    LogRepository,
    PlatformRepository
)
from core.database.integration import DatabaseIntegration


def test_database_integration():
    """Testa a integração com o banco de dados"""
    print("\n" + "="*60)
    print("TESTE DE INTEGRAÇÃO COM BANCO DE DADOS")
    print("="*60 + "\n")
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Inicializar banco
        print("1. Inicializando banco de dados...")
        integration = DatabaseIntegration(db)
        integration.init_database()
        print("   ✅ Banco de dados inicializado\n")
        
        # Testar PublicationRepository
        print("2. Testando PublicationRepository...")
        pub_repo = PublicationRepository(db)
        
        publication = pub_repo.create(
            title="Vídeo de Teste BD",
            description="Descrição do vídeo de teste",
            media_path="/videos/test.mp4",
            media_size_mb="50.5",
            media_format="mp4",
            duration_seconds="120",
            thumbnail_path="/videos/thumb.jpg"
        )
        print(f"   ✅ Publicação criada: {publication.id}")
        
        # Buscar publicação
        pub_found = pub_repo.get_by_id(str(publication.id))
        assert pub_found is not None
        assert pub_found.title == "Vídeo de Teste BD"
        print(f"   ✅ Publicação encontrada: {pub_found.title}")
        
        # Testar ScheduleRepository
        print("\n3. Testando ScheduleRepository...")
        schedule_repo = ScheduleRepository(db)
        
        scheduled_at = datetime.utcnow() + timedelta(hours=1)
        schedule = schedule_repo.create(
            publication_id=str(publication.id),
            scheduled_at=scheduled_at,
            status="pending"
        )
        print(f"   ✅ Agendamento criado: {schedule.id}")
        
        # Buscar agendamentos
        schedules = schedule_repo.get_by_publication_id(str(publication.id))
        assert len(schedules) == 1
        print(f"   ✅ Agendamentos encontrados: {len(schedules)}")
        
        # Testar ResultRepository
        print("\n4. Testando ResultRepository...")
        result_repo = ResultRepository(db)
        
        result = result_repo.create(
            publication_id=str(publication.id),
            platform_name="youtube",
            success=True,
            message="Publicado com sucesso",
            post_url="https://youtube.com/watch?v=123",
            published_at=datetime.utcnow()
        )
        print(f"   ✅ Resultado criado: {result.id}")
        
        # Buscar resultados
        results = result_repo.get_by_publication_id(str(publication.id))
        assert len(results) == 1
        print(f"   ✅ Resultados encontrados: {len(results)}")
        
        # Testar LogRepository
        print("\n5. Testando LogRepository...")
        log_repo = LogRepository(db)
        
        log = log_repo.create(
            level="INFO",
            message="Teste de log",
            module="test_database",
            publication_id=str(publication.id),
            extra_data='{"test": true}'
        )
        print(f"   ✅ Log criado: {log.id}")
        
        # Buscar logs
        logs = log_repo.get_by_publication_id(str(publication.id))
        assert len(logs) == 1
        print(f"   ✅ Logs encontrados: {len(logs)}")
        
        # Testar PlatformRepository
        print("\n6. Testando PlatformRepository...")
        platform_repo = PlatformRepository(db)
        
        # Listar plataformas
        platforms = platform_repo.get_all()
        print(f"   ✅ Plataformas encontradas: {len(platforms)}")
        for platform in platforms:
            print(f"      - {platform.name}: {platform.enabled}")
        
        # Testar DatabaseIntegration
        print("\n7. Testando DatabaseIntegration...")

        # Salvar publicação via integração (publication_id é gerado internamente)
        pub2 = integration.save_publication(
            title="Vídeo Integração",
            description="Teste de integração",
            media_path="/videos/test2.mp4",
            media_size_mb="30.0",
            media_format="mp4"
        )
        print(f"   ✅ Publicação salva via integração: {pub2.id}")
        
        # Salvar agendamento
        schedule2 = integration.save_schedule(
            publication_id=str(pub2.id),
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            status="pending"
        )
        print(f"   ✅ Agendamento salvo via integração: {schedule2.id}")
        
        # Salvar resultado
        result2 = integration.save_result(
            publication_id=str(pub2.id),
            platform_name="instagram",
            success=True,
            message="Publicado com sucesso"
        )
        print(f"   ✅ Resultado salvo via integração: {result2.id}")
        
        # Salvar log
        log2 = integration.save_log(
            level="INFO",
            message="Log de integração",
            module="integration_test",
            publication_id=str(pub2.id)
        )
        print(f"   ✅ Log salvo via integração: {log2.id}")
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES DE BANCO DE DADOS PASSARAM!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro nos testes: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Fechar sessão
        db.close()


if __name__ == "__main__":
    test_database_integration()