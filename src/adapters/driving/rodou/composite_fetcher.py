"""
Composite Fetcher para o Ro-DOU

Agrupa múltiplos adapters do Ro-DOU (DOU, INLABS) em um único fetcher.
"""

import logging
from typing import List, Dict, Any, Optional

from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult

logger = logging.getLogger(__name__)


class RodouCompositeFetcher(FetcherPort):
    """
    Fetcher composto que executa múltiplos adapters do Ro-DOU.
    
    Permite executar todas as fontes (DOU, INLABS) em uma única chamada,
    consolidando os resultados.
    """
    
    def __init__(self, adapters: List[Any]):
        """
        Inicializa o fetcher composto.
        
        Args:
            adapters: Lista de adapters do Ro-DOU (DouAdapter, InlabsAdapter)
        """
        self.adapters = adapters
        logger.info(f"RodouCompositeFetcher initialized with {len(adapters)} adapter(s)")
    
    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca usando todos os adapters e retorna o primeiro resultado.
        
        Args:
            kwargs: Parâmetros de busca
            
        Returns:
            Primeiro FetchResult encontrado ou erro se nenhum
        """
        all_results = self.fetch(kwargs)
        if all_results:
            return all_results[0]
        else:
            return FetchResult(
                success=False,
                error="Nenhum resultado encontrado em nenhum adapter do Ro-DOU"
            )
    
    def validar(self, identifier: str) -> bool:
        """
        Valida um identifier em todos os adapters.
        
        Args:
            identifier: URN a validar
            
        Returns:
            True se algum adapter validar o identifier
        """
        for adapter in self.adapters:
            try:
                if hasattr(adapter, 'validar') and adapter.validar(identifier):
                    return True
            except Exception:
                continue
        return False
    
    def fetch(self, params: Optional[Dict[str, Any]] = None) -> List[FetchResult]:
        """
        Executa o fetch em todos os adapters e consolida os resultados.
        
        Args:
            params: Parâmetros opcionais (ex: query, date_range, sections)
            
        Returns:
            Lista consolidada de FetchResult de todos os adapters
        """
        all_results: List[FetchResult] = []
        
        for adapter in self.adapters:
            try:
                logger.info(f"Executando adapter: {adapter.__class__.__name__}")
                results = adapter.fetch(params)
                # Converte resultados para o formato correto se necessário
                for r in results:
                    if isinstance(r, dict):
                        all_results.append(FetchResult(success=True, data=r))
                    else:
                        all_results.append(r)
                logger.info(f"  -> {len(results)} registros extraídos")
            except Exception as e:
                logger.warning(f"Erro no adapter {adapter.__class__.__name__}: {e}")
                # Continua com os próximos adapters mesmo se um falhar
        
        logger.info(f"Total consolidado: {len(all_results)} registros")
        return all_results

