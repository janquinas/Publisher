"""
Script de inicialização do banco de dados
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.config import engine, Base
from core.database.models import (
    PublicationDB,
    ScheduleDB,
    ResultDB,
    LogDB,
    PlatformDB,
    UserDB
)


def init_database():
    """
    Inicializa o banco de dados criando todas as tabelas
    """
    print("Inicializando banco de dados...")
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        
        # Listar tabelas criadas
        tables = Base.metadata.tables.keys()
        print(f"\nTabelas criadas: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        print("\n✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()