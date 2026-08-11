"""
Verificador de credenciais do .env

Uso:
    python scripts/check_credentials.py

Mostra quais plataformas estao prontas para o fluxo OAuth e o que falta preencher.
Nunca imprime o valor completo dos segredos (apenas mascarado).
Guia de obtencao das chaves: docs/guia-api-keys.md
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    print("[ERRO] Pacote python-dotenv nao instalado. Rode: pip install -r requirements.txt")
    sys.exit(1)

ENV_PATH = ROOT / ".env"

# (nome exibido, [vars obrigatorias], var de redirect, portal)
PLATFORMS = [
    ("Google (login do app)", ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
     "GOOGLE_REDIRECT_URI", "https://console.cloud.google.com/apis/credentials"),
    ("YouTube", ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
     "YOUTUBE_REDIRECT_URI", "https://console.cloud.google.com/apis/credentials"),
    ("Facebook", ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET"],
     "FACEBOOK_REDIRECT_URI", "https://developers.facebook.com/apps"),
    ("Instagram", ["INSTAGRAM_CLIENT_ID", "INSTAGRAM_CLIENT_SECRET"],
     "INSTAGRAM_REDIRECT_URI", "https://developers.facebook.com/apps"),
    ("TikTok", ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
     "TIKTOK_REDIRECT_URI", "https://developers.tiktok.com/apps"),
    ("Kwai (token manual)", ["KWAI_CLIENT_ID", "KWAI_CLIENT_SECRET"],
     "KWAI_REDIRECT_URI", "sem OAuth publico - use POST /api/platforms/kwai/connect"),
]

OPTIONAL_GROUPS = [
    ("SMTP (e-mails de recuperacao)", ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"]),
]


def mask(value: str) -> str:
    """Mascara o segredo, mostrando apenas inicio e fim."""
    if not value:
        return "(vazio)"
    if len(value) <= 8:
        return value[0] + "*" * (len(value) - 1)
    return f"{value[:4]}...{value[-4:]} ({len(value)} chars)"


def is_filled(value: str) -> bool:
    """Considera vazio, placeholder ou texto de exemplo como nao preenchido."""
    if not value or not value.strip():
        return False
    v = value.strip().lower()
    placeholders = ("seu_", "sua_", "your_", "changeme", "xxx", "...", "<", "cole_aqui")
    return not any(v.startswith(p) or v == p for p in placeholders)


def main() -> int:
    print("=" * 62)
    print(" Verificacao de credenciais - Automated Publishing Agent")
    print("=" * 62)

    if not ENV_PATH.exists():
        print(f"\n[ERRO] Arquivo .env nao encontrado em {ENV_PATH}")
        print("       Copie o modelo:  copy .env.example .env")
        return 1

    load_dotenv(ENV_PATH, override=True)
    print(f"\nArquivo lido: {ENV_PATH}\n")

    ready, pending = [], []

    print("--- REDES SOCIAIS / OAUTH ---\n")
    for name, required, redirect_var, portal in PLATFORMS:
        missing = [v for v in required if not is_filled(os.getenv(v, ""))]
        ok = not missing
        icon = "[OK]  " if ok else "[--]  "
        print(f"{icon}{name}")

        for var in required:
            val = os.getenv(var, "")
            status = mask(val) if is_filled(val) else "(NAO PREENCHIDO)"
            print(f"        {var} = {status}")

        redirect_val = os.getenv(redirect_var, "")
        print(f"        {redirect_var} = {redirect_val or '(usando padrao localhost)'}")

        if ok:
            ready.append(name)
        else:
            pending.append((name, missing, portal))
        print()

    print("--- OPCIONAIS ---\n")
    for name, required in OPTIONAL_GROUPS:
        missing = [v for v in required if not is_filled(os.getenv(v, ""))]
        icon = "[OK]  " if not missing else "[--]  "
        detail = "configurado" if not missing else f"faltam: {', '.join(missing)}"
        print(f"{icon}{name}: {detail}")

    print("\n" + "=" * 62)
    print(f" Prontas: {len(ready)}/{len(PLATFORMS)}")
    if ready:
        print(f"   -> {', '.join(ready)}")
    if pending:
        print("\n Pendentes:")
        for name, missing, portal in pending:
            print(f"   - {name}: falta {', '.join(missing)}")
            print(f"     portal: {portal}")
    print("=" * 62)
    print("\nPasso a passo detalhado: docs/guia-api-keys.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
