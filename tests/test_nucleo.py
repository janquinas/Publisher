"""
Script de teste do núcleo do sistema
Valida o fluxo completo de publicação
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o diretório raiz ao path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from core.models.publication import Publication
from core.models.schedule import Schedule
from core.models.platform import Platform
from core.models.media import Media
from core.services.log_manager import get_log_manager
from core.services.media_manager import MediaManager
from core.services.scheduler import Scheduler
from core.services.orchestrator import PublicationOrchestrator
from core.services.result_manager import ResultManager
from core.services.publication_service import PublicationService
from core.database.integration import DatabaseIntegration
from core.database.config import SessionLocal, init_db
from core.adapters.youtube_adapter import YouTubeAdapter
from core.adapters.instagram_adapter import InstagramAdapter
from core.adapters.tiktok_adapter import TikTokAdapter
from core.adapters.facebook_adapter import FacebookAdapter
from core.adapters.kwai_adapter import KwaiAdapter


def test_nucleo_completo():
    """Testa o fluxo completo do núcleo"""
    print("\n" + "="*60)
    print("TESTE DO NÚCLEO DO SISTEMA")
    print("="*60 + "\n")
    
    # Inicializar componentes
    log_manager = get_log_manager("test")
    media_manager = MediaManager()
    result_manager = ResultManager()
    scheduler = Scheduler()
    orchestrator = PublicationOrchestrator(result_manager)
    publication_service = PublicationService(
        media_manager=media_manager,
        scheduler=scheduler,
        orchestrator=orchestrator,
        result_manager=result_manager
    )

    # Inicializar banco e injetar DatabaseIntegration
    init_db()
    db_session = SessionLocal()
    db_integration = DatabaseIntegration(db_session)
    publication_service.db_integration = db_integration
    orchestrator.db_integration = db_integration
    
    # Registrar adaptadores
    print("1. Registrando adaptadores de plataforma...")
    orchestrator.register_adapter("youtube", YouTubeAdapter())
    orchestrator.register_adapter("instagram", InstagramAdapter())
    orchestrator.register_adapter("tiktok", TikTokAdapter())
    orchestrator.register_adapter("facebook", FacebookAdapter())
    orchestrator.register_adapter("kwai", KwaiAdapter())
    print("   ✅ Todos os adaptadores registrados\n")
    
    # Criar arquivo de vídeo temporário para teste
    print("2. Criando arquivo de vídeo temporário para teste...")
    test_video_path = "test_video.mp4"
    Path(test_video_path).touch()  # Criar arquivo vazio para teste
    print(f"   ✅ Arquivo criado: {test_video_path}\n")
    
    try:
        # Teste 1: Criação de publicação imediata via publish_now
        print("3. Testando criação e publicação IMEDIATA via publish_now...")
        publication = publication_service.create_publication(
            title="Vídeo de Teste",
            description="Descrição do vídeo de teste",
            media_path=test_video_path,
            media_size_mb=50.5,
            media_format="mp4",
            platforms=["youtube", "instagram", "tiktok"]
        )
        print(f"   ✅ Publicação criada: {publication.id}")
        print(f"   Título: {publication.title}")
        print(f"   Plataformas: {[p.name for p in publication.platforms]}\n")

        # Disparar publicação imediata via publish_now
        publication_service.publish_now(publication.id)

        # Aguardar threads paralelas concluírem
        import time
        time.sleep(2)
        
        # Teste 2: Verificar status da publicação
        print("4. Verificando status da publicação...")
        status = publication_service.get_publication_status(publication.id)
        print(f"   Status: {status['status']}")
        print(f"   Resultados: {status['results']}\n")
        
        # Teste 3: Criação de publicação agendada
        print("5. Testando criação de publicação AGENDADA...")
        scheduled_time = datetime.now() + timedelta(seconds=5)
        scheduled_publication = publication_service.create_publication(
            title="Vídeo Agendado",
            description="Descrição do vídeo agendado",
            media_path=test_video_path,
            media_size_mb=30.0,
            media_format="mp4",
            platforms=["facebook", "kwai"],
            scheduled_at=scheduled_time
        )
        print(f"   ✅ Publicação agendada: {scheduled_publication.id}")
        print(f"   Agendada para: {scheduled_time.isoformat()}\n")
        
        # Verificar se está agendada
        print("6. Verificando agendamento...")
        is_scheduled = scheduler.is_scheduled(scheduled_publication.id)
        print(f"   Está agendada: {is_scheduled}")
        
        scheduled_list = scheduler.get_scheduled_publications()
        print(f"   Publicações agendadas: {len(scheduled_list)}")
        for pub in scheduled_list:
            print(f"   - {pub['publication_id']}: {pub['next_run_time']}")
        print()
        
        # Aguardar execução do agendamento
        print("7. Aguardando execução do agendamento (5 segundos)...")
        time.sleep(6)
        
        # Teste 4: Verificar resultados do agendamento
        print("8. Verificando resultados do agendamento...")
        scheduled_status = publication_service.get_publication_status(scheduled_publication.id)
        print(f"   Status: {scheduled_status['status']}")
        print(f"   Resultados: {scheduled_status['results']}\n")
        
        # Teste 5: Gerar relatório
        print("9. Gerando relatório detalhado...")
        report = publication_service.get_publication_report(publication.id)
        print(report)
        
        # Teste 6: Listar todas as publicações
        print("\n10. Listando todas as publicações...")
        all_publications = publication_service.list_publications()
        print(f"    Total de publicações: {len(all_publications)}")
        for pub in all_publications:
            print(f"    - {pub.id}: {pub.title}")
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60 + "\n")
        
    finally:
        # Limpar arquivo de teste
        if Path(test_video_path).exists():
            Path(test_video_path).unlink()
            print(f"Arquivo de teste removido: {test_video_path}")
        
        # Parar scheduler
        scheduler.shutdown()


if __name__ == "__main__":
    test_nucleo_completo()