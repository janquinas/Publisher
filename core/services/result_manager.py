"""
Result Manager - Consolidação de resultados das publicações
"""
from typing import Dict, List, Optional
from datetime import datetime
from ..models.result import Result


class ResultManager:
    """Gerenciador de resultados das publicações"""
    
    def __init__(self):
        self.results: Dict[str, List[Result]] = {}  # publication_id -> lista de resultados
        self.logger = None  # Será injetado
    
    def set_logger(self, logger):
        """Injeta logger"""
        self.logger = logger
    
    def add_result(self, publication_id: str, result: Result):
        """
        Adiciona um resultado de publicação
        
        Args:
            publication_id: ID da publicação
            result: Resultado da publicação
        """
        if publication_id not in self.results:
            self.results[publication_id] = []
        
        self.results[publication_id].append(result)
        
        if self.logger:
            self.logger.info(
                "Resultado adicionado",
                publication_id=publication_id,
                platform=result.platform_name,
                success=result.success
            )
    
    def get_results(self, publication_id: str) -> List[Result]:
        """
        Obtém todos os resultados de uma publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de resultados
        """
        return self.results.get(publication_id, [])
    
    def get_successful_results(self, publication_id: str) -> List[Result]:
        """
        Obtém apenas os resultados bem-sucedidos
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de resultados bem-sucedidos
        """
        results = self.get_results(publication_id)
        return [r for r in results if r.success]
    
    def get_failed_results(self, publication_id: str) -> List[Result]:
        """
        Obtém apenas os resultados de falha
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de resultados de falha
        """
        results = self.get_results(publication_id)
        return [r for r in results if not r.success]
    
    def get_summary(self, publication_id: str) -> Dict:
        """
        Obtém resumo dos resultados
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Dict com resumo dos resultados
        """
        results = self.get_results(publication_id)
        
        total = len(results)
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        
        platforms_success = [r.platform_name for r in results if r.success]
        platforms_failed = [r.platform_name for r in results if not r.success]
        
        return {
            "publication_id": publication_id,
            "total_platforms": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "platforms_success": platforms_success,
            "platforms_failed": platforms_failed,
            "all_success": failed == 0 and total > 0,
            "has_failures": failed > 0
        }
    
    def get_detailed_report(self, publication_id: str) -> str:
        """
        Gera relatório detalhado dos resultados
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            String com relatório formatado
        """
        results = self.get_results(publication_id)
        summary = self.get_summary(publication_id)
        
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"RELATÓRIO DE PUBLICAÇÃO - {publication_id}")
        report.append(f"{'='*60}")
        report.append(f"Total de plataformas: {summary['total_platforms']}")
        report.append(f"Sucessos: {summary['successful']}")
        report.append(f"Falhas: {summary['failed']}")
        report.append(f"Taxa de sucesso: {summary['success_rate']:.1f}%")
        report.append(f"\n{'='*60}")
        report.append("DETALHAMENTO POR PLATAFORMA:")
        report.append(f"{'='*60}")
        
        for result in results:
            status = "✅ SUCESSO" if result.success else "❌ FALHA"
            report.append(f"\n{result.platform_name.upper()}: {status}")
            report.append(f"  Mensagem: {result.message}")
            if result.post_url:
                report.append(f"  URL: {result.post_url}")
            if result.error_code:
                report.append(f"  Código do erro: {result.error_code}")
            if result.published_at:
                report.append(f"  Publicado em: {result.published_at}")
        
        report.append(f"\n{'='*60}")
        
        return "\n".join(report)
    
    def clear_results(self, publication_id: str):
        """
        Limpa os resultados de uma publicação
        
        Args:
            publication_id: ID da publicação
        """
        if publication_id in self.results:
            del self.results[publication_id]
            if self.logger:
                self.logger.info("Resultados limpos", publication_id=publication_id)
    
    def clear_all_results(self):
        """Limpa todos os resultados"""
        self.results.clear()
        if self.logger:
            self.logger.info("Todos os resultados foram limpos")
    
    def get_error_messages(self, publication_id: str) -> List[str]:
        """
        Obtém todas as mensagens de erro de uma publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            Lista de mensagens de erro
        """
        failed_results = self.get_failed_results(publication_id)
        return [r.message for r in failed_results]
    
    def has_errors(self, publication_id: str) -> bool:
        """
        Verifica se houve erros em uma publicação
        
        Args:
            publication_id: ID da publicação
            
        Returns:
            True se houve erros, False caso contrário
        """
        return len(self.get_failed_results(publication_id)) > 0