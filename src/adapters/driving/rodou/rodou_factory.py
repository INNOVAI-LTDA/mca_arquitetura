"""
Factory para inicialização do Ro-DOU

Gerencia o ciclo de vida da instância única do Ro-DOU.
Fornece mock adapters quando o Airflow não está disponível.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RodouFactory:
    """
    Factory singleton para gerenciar a instância do Ro-DOU.

    O Ro-DOU é uma biblioteca externa que depende do Apache Airflow.
    Esta factory tenta carregar o Ro-DOU real, mas fallback para mock
    adapters quando o Airflow não está disponível.
    """

    _instance: Optional[Any] = None
    _initialized: bool = False
    _use_mock: bool = False

    @classmethod
    def get_instance(cls) -> Any:
        """
        Retorna a instância única do Ro-DOU ou mock.

        Returns:
            Instância do objeto Searcher do Ro-DOU ou MockSearcher
        """
        if not cls._initialized:
            try:
                # Tenta importar o Ro-DOU real (requer Airflow)
                from rodou.src.searchers import DOUSearcher, INLABSSearcher

                cls._instance = {
                    'dou': DOUSearcher(),
                    'inlabs': INLABSSearcher()
                }
                cls._use_mock = False
                cls._initialized = True
                logger.info("Ro-DOU instance initialized successfully with real searchers")

            except ImportError as e:
                logger.warning(f"Ro-DOU dependencies unavailable ({e}), using mock adapters")
                logger.warning("Ro-DOU functionality will operate in dry-run mode")
                
                # Fallback para mock adapters
                cls._instance = {
                    'dou': cls._create_mock_dou_searcher(),
                    'inlabs': cls._create_mock_inlabs_searcher()
                }
                cls._use_mock = True
                cls._initialized = True

        return cls._instance

    @classmethod
    def is_mock(cls) -> bool:
        """Retorna True se estiver usando mock adapters."""
        return cls._use_mock

    @staticmethod
    def _create_mock_dou_searcher() -> Any:
        """Cria um mock searcher para DOU."""
        class MockDOUSearcher:
            def search(self, term=None, date_from=None, date_to=None, sections=None, **kwargs):
                logger.info(f"[MOCK DOU] Search called with term='{term}'")
                # Retorna dados simulados para demonstração
                return [
                    {
                        "title": f"Normativo MOCK DOU sobre {term or 'conformidade aduaneira'}",
                        "date": "2024-01-15",
                        "section": str(sections[0]) if sections else "1",
                        "url": "https://www.in.gov.br/dou/mock-document",
                        "content": f"Conteúdo simulado sobre {term or 'conformidade aduaneira'}",
                        "summary": "Resumo mock do normativo DOU"
                    }
                ]
        return MockDOUSearcher()

    @staticmethod
    def _create_mock_inlabs_searcher() -> Any:
        """Cria um mock searcher para INLABS."""
        class MockINLABSSearcher:
            def search(self, term=None, date_from=None, date_to=None, sections=None, **kwargs):
                logger.info(f"[MOCK INLABS] Search called with term='{term}'")
                # Retorna dados simulados para demonstração
                return [
                    {
                        "title": f"Portaria INLABS MOCK sobre {term or 'laboratórios'}",
                        "date": "2024-02-20",
                        "section": str(sections[0]) if sections else "1",
                        "url": "https://www.gov.br/inlabs/mock-document",
                        "content": f"Conteúdo simulado sobre {term or 'INLABS'}",
                        "summary": "Resumo mock da portaria INLABS"
                    }
                ]
        return MockINLABSSearcher()

    @classmethod
    def reset(cls):
        """Reseta o estado da factory (útil para testes)."""
        cls._instance = None
        cls._initialized = False
        cls._use_mock = False
