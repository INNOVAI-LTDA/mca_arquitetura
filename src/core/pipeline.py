"""
Pipeline de Ingestão do MCA

Responsável por coordenar o fluxo de dados entre os adapters de origem
(Senado, NCM, Ro-DOU) e o adapter de destino (Neo4j).
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.domain.ports import FetcherPort, IngestPort
from src.domain.entities import FetchResult, NormativeWork

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Resultado da execução do pipeline."""
    total_fetched: int = 0
    total_ingested: int = 0
    total_errors: int = 0
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class Pipeline:
    """
    Pipeline genérico para ingestão de dados normativos.
    
    Segue o padrão: Fetch -> Transform -> Validate -> Ingest
    """
    
    def __init__(self, fetcher: FetcherPort, storage: IngestPort):
        self.fetcher = fetcher
        self.storage = storage
    
    def execute(self, params: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> PipelineResult:
        """
        Executa o pipeline de ingestão.
        
        Args:
            params: Parâmetros específicos para o fetcher
            dry_run: Se True, apenas valida sem persistir
            
        Returns:
            PipelineResult com estatísticas da execução
        """
        result = PipelineResult()
        
        try:
            # Fase 1: Fetch
            logger.info("Fase 1: Extraindo dados...")
            fetched_data: List[FetchResult] = self.fetcher.fetch(params)
            result.total_fetched = len(fetched_data)
            
            if not fetched_data:
                logger.info("Nenhum dado encontrado para extração.")
                return result
            
            # Fase 2: Transform & Validate
            logger.info("Fase 2: Transformando e validando dados...")
            normative_works: List[NormativeWork] = []
            
            for item in fetched_data:
                try:
                    work = self._transform_to_normative_work(item)
                    normative_works.append(work)
                except Exception as e:
                    logger.warning(f"Erro ao transformar item {item}: {e}")
                    result.total_errors += 1
            
            # Fase 3: Ingest
            if dry_run:
                logger.info("Dry-run: Skipping ingestion phase.")
                logger.info(f"Dados prontos para ingestão: {len(normative_works)} registros")
            else:
                logger.info("Fase 3: Persistindo dados no Neo4j...")
                ingested_count = self.storage.ingest(normative_works)
                result.total_ingested = ingested_count
            
            logger.info(f"Pipeline concluído: {result.total_fetched} extraídos, "
                       f"{result.total_ingested} ingeridos, {result.total_errors} erros")
                       
        except Exception as e:
            logger.exception(f"Erro crítico no pipeline: {e}")
            result.total_errors += 1
        
        return result
    
    def _transform_to_normative_work(self, fetch_result: FetchResult) -> NormativeWork:
        """
        Transforma um FetchResult em um NormativeWork.
        
        Subclasses podem sobrescrever este método para lógica específica.
        """
        # Implementação genérica - assume que fetch_result já tem estrutura compatível
        return NormativeWork(
            urn=fetch_result.urn,
            title=fetch_result.title,
            date=fetch_result.date,
            level=fetch_result.level,
            metadata=fetch_result.metadata
        )
