"""
Configuração do Backend
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Aplicação
    APP_NAME: str = "Automated Publishing Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # CORS - aceita string separada por vírgula ou JSON array do .env
    CORS_ORIGINS: str = "*"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: str = "*"
    CORS_HEADERS: str = "*"

    @property
    def cors_origins_list(self) -> list:
        """
        Converte CORS_ORIGINS (str) em lista.
        AVISO: usar '*' com CORS_CREDENTIALS=True é inválido pelo spec do CORS
        e causa erro no browser. Em produção, defina o domínio real.
        """
        origins = self.CORS_ORIGINS.strip()
        if not origins:
            return ["http://localhost:8000"]
        if origins == "*":
            if self.CORS_CREDENTIALS:
                import logging
                logging.getLogger("backend.config").warning(
                    "CORS_ORIGINS='*' com CORS_CREDENTIALS=True é inválido em produção. "
                    "Defina CORS_ORIGINS com o domínio real (ex: https://seudominio.com)."
                )
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    @property
    def cors_methods_list(self) -> list:
        """Converte CORS_METHODS (str) em lista."""
        if self.CORS_METHODS.strip() == "*":
            return ["*"]
        return [m.strip() for m in self.CORS_METHODS.split(",") if m.strip()]

    @property
    def cors_headers_list(self) -> list:
        """Converte CORS_HEADERS (str) em lista."""
        if self.CORS_HEADERS.strip() == "*":
            return ["*"]
        return [h.strip() for h in self.CORS_HEADERS.split(",") if h.strip()]
    
    # Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: list = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./automated_publishing.db"
    DB_TYPE: str = "sqlite"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "automated_publishing"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    
    # SMTP (para redefinição de senha / e-mail)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@publisher.com"
    EMAIL_RESET_URL: str = "http://localhost:8000/app/redefinir-senha.html"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
