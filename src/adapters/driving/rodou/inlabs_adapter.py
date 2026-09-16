"""
Adapter INLABS via Ro-DOU

Implementa a busca específica para normativos do INLABS.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult
from .rodou_factory import RodouFactory

logger = logging.getLogger(__name__)


class InlabsAdapter(FetcherPort):
    """
    Adapter para busca de normativos específicos do INLABS.

    Utiliza o Ro-DOU com filtros especializados para encontrar
    normativos relacionados ao INLABS (Instituto Nacional de
    Laboratórios de Saúde).
    """

    def __init__(self, rodou_factory: RodouFactory = None):
        """
        Inicializa o adapter INLABS.

        Args:
            rodou_factory: Factory para obter instância do Ro-DOU
        """
        self.factory = rodou_factory or RodouFactory()
        self.searchers = self.factory.get_instance()
        self.searcher = self.searchers.get('inlabs') if isinstance(self.searchers, dict) else self.searchers

    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca um normativo específico do INLABS.

        Args:
            query: Termo de busca adicional (opcional)

        Returns:
            FetchResult com o primeiro resultado encontrado
        """
        try:
            results = self.fetch({"query": kwargs.get("query", ""), "limit": 1})
            if results:
                return results[0]
            else:
                return FetchResult(
                    success=False,
                    error="Nenhum normativo INLABS encontrado"
                )
        except Exception as e:
            return FetchResult(
                success=False,
                error=str(e)
            )

    def validar(self, identifier: str) -> bool:
        """
        Valida se um identifier (URN) existe na fonte.

        Args:
            identifier: URN do normativo INLABS

        Returns:
            True se existir, False caso contrário
        """
        # Implementação simplificada - valida formato do URN
        try:
            # Formato: urn:inlabs:{section}:{date}:{hash}
            parts = identifier.split(":")
            if len(parts) >= 6 and parts[1] == "inlabs":
                return True
        except Exception:
            pass
        return False

    def fetch(self, params: Optional[Dict[str, Any]] = None) -> List[FetchResult]:
        """
        Executa busca específica para INLABS.

        Args:
            params: Parâmetros de busca:
                - query: Termo de busca adicional (opcional)
                - date_from: Data inicial (opcional)
                - date_to: Data final (opcional)

        Returns:
            Lista de FetchResult com os normativos do INLABS
        """
        if not self.searcher:
            logger.warning("Ro-DOU não disponível, retornando lista vazia")
            return []

        # Query padrão para INLABS + termos adicionais
        base_query = "INLABS OR \"Instituto Nacional de Laboratórios\""
        extra_query = params.get("query", "") if params else ""

        if extra_query:
            query = f"{base_query} AND {extra_query}"
        else:
            query = base_query

        date_from = params.get("date_from") if params else None
        date_to = params.get("date_to") if params else None

        logger.info(f"Buscando normativos INLABS: query='{query}'")

        try:
            # Busca no Ro-DOU com foco em INLABS
            results = self.searcher.search(
                term=query,
                date_from=date_from,
                date_to=date_to,
                sections=[1, 2, 3]  # Todas as seções
            )

            fetch_results = []
            for item in results:
                fetch_result = self._transform_item(item)
                if fetch_result:
                    fetch_results.append(fetch_result)

            logger.info(f"INLABS: {len(fetch_results)} resultados encontrados")
            return fetch_results

        except Exception as e:
            logger.exception(f"Erro na busca INLABS: {e}")
            return []

    def _transform_item(self, item: Dict[str, Any]) -> Optional[FetchResult]:
        """
        Transforma um resultado bruto do Ro-DOU em FetchResult.

        Args:
            item: Dicionário com dados brutos do Ro-DOU

        Returns:
            FetchResult estruturado ou None se inválido
        """
        try:
            title = item.get("title", "")
            date_str = item.get("date", "")
            url = item.get("url", "")
            section = item.get("section", "")
            content = item.get("content", "")

            # Gera URN único para INLABS
            urn = f"urn:inlabs:{section}:{date_str.replace('-', '')}:{hash(title) % 10000:04d}"

            # Parse da data
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                date = datetime.now().date()

            return FetchResult(
                success=True,
                data={
                    "urn": urn,
                    "title": title,
                    "date": date,
                    "level": "L6",
                    "metadata": {
                        "source": "INLABS",
                        "section": section,
                        "url": url,
                        "content": content,
                        "original": item,
                        "specialization": "inlabs"
                    }
                }
            )

        except Exception as e:
            logger.warning(f"Erro ao transformar item INLABS: {e}")
            return None
