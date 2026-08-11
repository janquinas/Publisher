"""
Configurações do núcleo do sistema
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Configurações de mídia
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
MAX_VIDEO_SIZE_MB = 500

# Configurações de agendamento
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "America/Sao_Paulo")