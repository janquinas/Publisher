"""
Configuração do banco de dados
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

load_dotenv()


def _build_database_url() -> str:
    """
    Monta a URL de conexão com o banco de dados.

    Prioriza DATABASE_URL. Caso contrário, monta dinamicamente uma URL
    PostgreSQL a partir de DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.
    Se nenhuma configuração PostgreSQL estiver presente, usa SQLite local.
    """
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url

    db_type = os.getenv("DB_TYPE", "").strip().lower()
    db_host = os.getenv("DB_HOST", "").strip()
    db_port = os.getenv("DB_PORT", "").strip()
    db_name = os.getenv("DB_NAME", "").strip()
    db_user = os.getenv("DB_USER", "").strip()
    db_password = os.getenv("DB_PASSWORD", "").strip()

    if db_type in ("postgresql", "postgres") and db_host and db_name:
        port_part = f":{db_port}" if db_port else ""
        password_part = f":{db_password}" if db_user else ""
        user_part = f"{db_user}{password_part}" if db_user else ""
        return f"postgresql://{user_part}@{db_host}{port_part}/{db_name}"

    # SQLite para desenvolvimento local
    return os.getenv("SQLITE_DB_PATH", "sqlite:///./automated_publishing.db")


# URL de conexão com o banco de dados
DATABASE_URL = _build_database_url()

# Engine do SQLAlchemy
# Para SQLite, habilita check_same_thread=False (necessário para uso web)
# e usa NullPool para evitar manter conexões abertas entre sessões.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    engine = create_engine(DATABASE_URL)

# SessionLocal para criar sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados

    Yields:
        Session: Sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Também executa migrações manuais para adicionar colunas novas a tabelas existentes.
    """
    from core.database.models import (
        PublicationDB,
        ScheduleDB,
        ResultDB,
        LogDB,
        PlatformDB,
        UserDB
    )
    Base.metadata.create_all(bind=engine)

    # Migração manual: adicionar coluna 'platforms' à tabela publications se não existir
    # Necessário para bancos SQLite existentes criados antes desta coluna ser adicionada
    try:
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            if DATABASE_URL.startswith("sqlite"):
                result = conn.execute(
                    __import__("sqlalchemy").text("PRAGMA table_info(publications)")
                )
                columns = [row[1] for row in result]
                if "platforms" not in columns:
                    conn.execute(
                        __import__("sqlalchemy").text(
                            "ALTER TABLE publications ADD COLUMN platforms TEXT DEFAULT '[]'"
                        )
                    )
                    conn.commit()
                if "is_media_only" not in columns:
                    conn.execute(
                        __import__("sqlalchemy").text(
                            "ALTER TABLE publications ADD COLUMN is_media_only INTEGER NOT NULL DEFAULT 0"
                        )
                    )
                    conn.commit()
            else:
                # PostgreSQL / outros — usar information_schema
                result = conn.execute(
                    __import__("sqlalchemy").text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='publications' AND column_name='platforms'"
                    )
                )
                if not result.fetchone():
                    conn.execute(
                        __import__("sqlalchemy").text(
                            "ALTER TABLE publications ADD COLUMN platforms TEXT DEFAULT '[]'"
                        )
                    )
                    conn.commit()
                result2 = conn.execute(
                    __import__("sqlalchemy").text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='publications' AND column_name='is_media_only'"
                    )
                )
                if not result2.fetchone():
                    conn.execute(
                        __import__("sqlalchemy").text(
                            "ALTER TABLE publications ADD COLUMN is_media_only BOOLEAN NOT NULL DEFAULT FALSE"
                        )
                    )
                    conn.commit()
    except Exception:
        pass  # Se a tabela ainda não existir, create_all acima a cria com a coluna


def dispose_db():
    """Fecha conexões ativas do engine para permitir reinicialização do banco."""
    engine.dispose()