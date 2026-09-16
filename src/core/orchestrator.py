"""
Orquestrador do MCA

Responsável por coordenar múltiplos pipelines de diferentes fontes
(Senado, NCM, Ro-DOU) em uma única execução coesa.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from src.domain.ports import IngestPort
from src.core.pipeline import Pipeline, PipelineResult

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Resultado consolidado da orquestração."""
    senado_result: Optional[PipelineResult] = None
    ncm_result: Optional[PipelineResult] = None
    rodou_result: Optional[PipelineResult] = None
    
    @property
    def total_fetched(self) -> int:
        return sum(
            r.total_fetched for r in [self.senado_result, self.ncm_result, self.rodou_result]
            if r is not None
        )
    
    @property
    def total_ingested(self) -> int:
        return sum(
            r.total_ingested for r in [self.senado_result, self.ncm_result, self.rodou_result]
            if r is not None
        )
    
    @property
    def total_errors(self) -> int:
        return sum(
            r.total_errors for r in [self.senado_result, self.ncm_result, self.rodou_result]
            if r is not None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_fetched": self.total_fetched,
            "total_ingested": self.total_ingested,
            "total_errors": self.total_errors,
            "details": {
                "senado": self.senado_result.details if self.senado_result else None,
                "ncm": self.ncm_result.details if self.ncm_result else None,
                "rodou": self.rodou_result.details if self.rodou_result else None,
            }
        }


class Orchestrator:
    """
    Orquestra a execução de múltiplos adapters de origem.
    
    Coordena a ingestão de dados em uma hierarquia de 6 níveis:
    - Níveis 1-4: Senado (EMC, DLG, LEI, DEC)
    - Nível 5: NCM (Tabela de Classificação Fiscal)
    - Nível 6: Ro-DOU (Diário Oficial)
    
    Todos os dados convergem para o storage Neo4j, garantindo a ordem
    correta e validação dos invariantes.
    """
    
    def __init__(
        self,
        storage: IngestPort,
        senado_adapters: Optional[List[Any]] = None,
        ncm_adapters: Optional[List[Any]] = None,
        rodou_adapters: Optional[List[Any]] = None
    ):
        """
        Inicializa o orquestrador.
        
        Args:
            storage: Adapter de armazenamento (Neo4j)
            senado_adapters: Lista de adapters do Senado (EMC, DLG, LEI, DEC)
            ncm_adapters: Lista de adapters do NCM
            rodou_adapters: Lista de adapters do Ro-DOU (DOU, INLABS)
        """
        self.storage = storage
        self.senado_adapters = senado_adapters or []
        self.ncm_adapters = ncm_adapters or []
        self.rodou_adapters = rodou_adapters or []
        
        logger.info(f"Orchestrator initialized with:")
        logger.info(f"  - {len(self.senado_adapters)} Senado adapter(s)")
        logger.info(f"  - {len(self.ncm_adapters)} NCM adapter(s)")
        logger.info(f"  - {len(self.rodou_adapters)} Ro-DOU adapter(s)")
    
    def run(self, dry_run: bool = False) -> OrchestrationResult:
        """
        Executa todos os pipelines configurados.
        
        Args:
            dry_run: Se True, executa sem persistir dados
            
        Returns:
            OrchestrationResult com resultados consolidados
        """
        logger.info("=" * 60)
        logger.info("Iniciando Orquestração MCA")
        logger.info("=" * 60)
        
        result = OrchestrationResult()
        
        # Executa pipeline do Senado (Níveis 1-4)
        if self.senado_adapters:
            logger.info("\n--- Pipeline Senado (Níveis 1-4) ---")
            result.senado_result = self._run_senado_pipeline(dry_run)
        
        # Executa pipeline do NCM (Nível 5 - Hierarquia de Classificação Fiscal)
        if self.ncm_adapters:
            logger.info("\n--- Pipeline NCM (Nível 5) ---")
            result.ncm_result = self._run_ncm_pipeline(dry_run)
        
        # Executa pipeline do Ro-DOU (Nível 6 - Inteligência Textual)
        if self.rodou_adapters:
            logger.info("\n--- Pipeline Ro-DOU (Nível 6) ---")
            result.rodou_result = self._run_rodou_pipeline(dry_run)
        
        # Resumo final
        logger.info("\n" + "=" * 60)
        logger.info("Resumo da Orquestração")
        logger.info("=" * 60)
        logger.info(f"Total Extraído: {result.total_fetched}")
        logger.info(f"Total Ingerido: {result.total_ingested}")
        logger.info(f"Total Erros:    {result.total_errors}")
        logger.info("=" * 60)
        
        return result
    
    def _run_senado_pipeline(self, dry_run: bool) -> PipelineResult:
        """Executa o pipeline combinado do Senado."""
        # Cria um fetcher composto para o Senado
        from src.adapters.driving.senado.composite_fetcher import SenadoCompositeFetcher
        
        fetcher = SenadoCompositeFetcher(self.senado_adapters)
        pipeline = Pipeline(fetcher, self.storage)
        return pipeline.execute(dry_run=dry_run)
    
    def _run_ncm_pipeline(self, dry_run: bool) -> PipelineResult:
        """Executa o pipeline do NCM."""
        # Usa o primeiro adapter NCM (normalmente só há um)
        if self.ncm_adapters:
            fetcher = self.ncm_adapters[0]
            pipeline = Pipeline(fetcher, self.storage)
            return pipeline.execute(dry_run=dry_run)
        
        return PipelineResult()
    
    def _run_rodou_pipeline(self, dry_run: bool) -> PipelineResult:
        """Executa o pipeline do Ro-DOU."""
        # Cria um fetcher composto para o Ro-DOU
        from src.adapters.driving.rodou.composite_fetcher import RodouCompositeFetcher
        
        fetcher = RodouCompositeFetcher(self.rodou_adapters)
        pipeline = Pipeline(fetcher, self.storage)
        return pipeline.execute(dry_run=dry_run)
