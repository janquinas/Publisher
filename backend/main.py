"""
Main - Ponto de entrada da aplicação Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.config import settings
from backend.controllers import (
    publication_controller,
    platform_controller,
    analytics_controller,
    auth_controller,
    health_controller,
    home_controller,
    media_controller,
)
from backend.exceptions.handlers import setup_exception_handlers
from core.database.config import init_db, dispose_db

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        description="API para automação de publicações em redes sociais",
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.cors_methods_list,
        allow_headers=settings.cors_headers_list,
    )

    # Arquivos estáticos
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")
    app.mount("/assets", StaticFiles(directory="frontend"), name="frontend-assets")

    # Exception handlers
    setup_exception_handlers(app)

    # Routers
    app.include_router(home_controller.router, tags=["Home"])
    app.include_router(health_controller.router, tags=["Health"])
    app.include_router(publication_controller.router, prefix="/api/publications", tags=["Publications"])
    app.include_router(platform_controller.router, prefix="/api/platforms", tags=["Platforms"])
    app.include_router(analytics_controller.router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(auth_controller.router, prefix="/api/auth", tags=["Auth"])
    app.include_router(media_controller.router, prefix="/api/media", tags=["Media"])

    # Rota para servir arquivos do frontend
    @app.get("/app/{path:path}")
    async def serve_frontend(path: str):
        """Serve o frontend estático."""
        from fastapi.responses import FileResponse
        import os

        frontend_path = f"frontend/{path}"
        if os.path.exists(frontend_path):
            return FileResponse(frontend_path)
        return FileResponse("frontend/index.html")

    # Rota raiz
    @app.get("/")
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/index.html")

    # ----------------------------------------------------------------
    # Startup: inicializar banco e scheduler UMA VEZ
    # ----------------------------------------------------------------
    @app.on_event("startup")
    async def startup_event():
        from backend.core_integration import CoreIntegration, _get_scheduler
        from core.database.config import SessionLocal

        # Criar tabelas (idempotente)
        init_db()

        db = SessionLocal()
        try:
            core = CoreIntegration(db)
            core.initialize()
        except Exception as e:
            print(f"Erro ao inicializar aplicação: {e}")
        finally:
            db.close()

    # ----------------------------------------------------------------
    # Shutdown: parar apenas o scheduler
    # ----------------------------------------------------------------
    @app.on_event("shutdown")
    async def shutdown_event():
        from backend.core_integration import _get_scheduler
        try:
            _get_scheduler().shutdown()
        except Exception as e:
            print(f"Erro ao finalizar scheduler: {e}")
        finally:
            dispose_db()

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
