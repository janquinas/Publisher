"""
Analytics Controller - Endpoints para dados estatisticos
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from backend.auth import get_current_session
from backend.core_integration import get_core_integration
from core.database.config import get_db

router = APIRouter()


@router.get("/overview")
async def get_overview(db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Visao geral: total de publicacoes, resultados, taxa de sucesso e total de midia."""
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()

        publications  = db_integration.publication_repo.get_all()
        all_results   = db_integration.result_repo.get_all()

        total_publications = len(publications)
        total_results      = len(all_results)
        successful = sum(1 for r in all_results if r.success)
        failed     = total_results - successful
        success_rate = round((successful / total_results * 100) if total_results > 0 else 0, 2)

        # Total de arquivos de midia — reutiliza a contagem já feita acima
        total_media = total_publications

        # Agendamentos pendentes
        pending_schedules = 0
        try:
            pending_schedules = len(db_integration.schedule_repo.get_pending_schedules())
        except Exception:
            pass

        return {
            "total_publications": total_publications,
            "total_results":      total_results,
            "total_media":        total_media,
            "pending_schedules":  pending_schedules,
            "successful":         successful,
            "failed":             failed,
            "success_rate":       success_rate,
            "timestamp":          datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter visao geral: {str(e)}")


@router.get("/by-platform")
async def get_by_platform(db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Estatisticas agrupadas por plataforma."""
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        all_results = db_integration.result_repo.get_all()

        platform_stats: Dict[str, Any] = {}
        for result in all_results:
            platform = getattr(result, "platform_name", "desconhecida") or "desconhecida"
            if platform not in platform_stats:
                platform_stats[platform] = {"total": 0, "successful": 0, "failed": 0}
            platform_stats[platform]["total"] += 1
            if result.success:
                platform_stats[platform]["successful"] += 1
            else:
                platform_stats[platform]["failed"] += 1

        for stats in platform_stats.values():
            stats["success_rate"] = round(
                (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0, 2
            )

        return {"platforms": platform_stats, "total_platforms": len(platform_stats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatisticas por plataforma: {str(e)}")


@router.get("/by-month")
async def get_by_month(months: int = 6, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """
    Agrupa publicacoes por mes nos ultimos N meses.
    Retorna lista de {year, month, month_name, count} ordenada do mais antigo para o mais recente.
    Usado pelo grafico de linha do frontend.
    """
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        publications = db_integration.publication_repo.get_all()

        now = datetime.utcnow()
        month_names = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                       "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

        # Montar mapa ano-mes → contagem
        counts: Dict[str, int] = {}
        for i in range(months - 1, -1, -1):
            # Mes alvo (retrocedendo i meses)
            target_month = (now.month - 1 - i) % 12 + 1
            target_year  = now.year + ((now.month - 1 - i) // 12)
            key = f"{target_year}-{target_month:02d}"
            counts[key] = 0

        for pub in publications:
            if pub.created_at:
                key = f"{pub.created_at.year}-{pub.created_at.month:02d}"
                if key in counts:
                    counts[key] += 1

        result_list = []
        for key, count in counts.items():
            year, month = int(key.split("-")[0]), int(key.split("-")[1])
            result_list.append({
                "year":       year,
                "month":      month,
                "month_name": month_names[month - 1],
                "count":      count,
            })

        return {"data": result_list, "total_months": len(result_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados mensais: {str(e)}")


@router.get("/success-rate")
async def get_success_rate(db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Taxa de sucesso geral."""
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        all_results = db_integration.result_repo.get_all()

        total      = len(all_results)
        successful = sum(1 for r in all_results if r.success)
        failed     = total - successful

        return {
            "total":        total,
            "successful":   successful,
            "failed":       failed,
            "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter taxa de sucesso: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(limit: int = 20, db=Depends(get_db), session: Dict = Depends(get_current_session)):
    """Atividade recente (logs do sistema)."""
    try:
        core = get_core_integration(db)
        db_integration = core.get_database_integration()
        recent_logs = db_integration.log_repo.get_recent_logs(limit)

        activity = [
            {
                "id":        str(log.id),
                "level":     log.level,
                "message":   log.message,
                "module":    log.module,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in recent_logs
        ]

        return {"activity": activity, "total": len(activity)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter atividade recente: {str(e)}")
