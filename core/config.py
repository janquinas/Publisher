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

# Configurações de plataformas
YOUTUBE_API_URL = os.getenv("YOUTUBE_API_URL", "https://www.googleapis.com/upload/youtube/v3/videos")
INSTAGRAM_API_URL = os.getenv("INSTAGRAM_API_URL", "https://graph.instagram.com/me/media")
TIKTOK_API_URL = os.getenv("TIKTOK_API_URL", "https://open-api.tiktok.com/video/upload/")
FACEBOOK_API_URL = os.getenv("FACEBOOK_API_URL", "https://graph.facebook.com/v18.0/me/videos")
KWAI_API_URL = os.getenv("KWAI_API_URL", "https://api.kwai.com/v1/video/upload")