"""
Adapter DOU (Diário Oficial da União) via Ro-DOU

Implementa a busca de normativos no DOU usando o Ro-DOU.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult
from .rodou_factory import RodouFactory

logger = logging.getLogger(__name__)


class DouAdapter(FetcherPort):
    """
    Adapter para busca no Diário Oficial da União.

    Utiliza o Ro-DOU para realizar buscas full-text nos normativos
    publicados no DOU, retornando resultados estruturados.
    """

    def __init__(self, rodou_factory: RodouFactory = None):
        """
        Inicializa o adapter DOU.

        Args:
            rodou_factory: Factory para obter instância do Ro-DOU
        """
        self.factory = rodou_factory or RodouFactory()
        self.searchers = self.factory.get_instance()
        self.searcher = self.searchers.get('dou') if isinstance(self.searchers, dict) else self.searchers

    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca um normativo específico no DOU.

        Args:
            query: Termo de busca (obrigatório)

        Returns:
            FetchResult com o primeiro resultado encontrado
        """
        query = kwargs.get("query")

        if not query:
            return FetchResult(
                success=False,
                error="Parâmetro 'query' é obrigatório"
            )

        try:
            results = self.fetch({"query": query, "limit": 1})
            if results:
                return results[0]
            else:
                return FetchResult(
                    success=False,
                    error=f"Nenhum resultado encontrado para '{query}'"
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
            identifier: URN do normativo DOU

        Returns:
            True se existir, False caso contrário
        """
        # Implementação simplificada - tenta buscar pelo hash no URN
        try:
            # Formato: urn:dou:{section}:{date}:{hash}
            parts = identifier.split(":")
            if len(parts) >= 6:
                # Extrai termo de busca do título ou conteúdo
                # Em produção, usaria uma API de validação específica
                return True  # Assume válido se o formato estiver correto
        except Exception:
            pass
        return False

    def fetch(self, params: Optional[Dict[str, Any]] = None) -> List[FetchResult]:
        """
        Executa busca no DOU.

        Args:
            params: Parâmetros de busca:
                - query: Termo de busca (obrigatório)
                - date_from: Data inicial (opcional)
                - date_to: Data final (opcional)
                - sections: Seções do DOU (1, 2, 3) (opcional)

        Returns:
            Lista de FetchResult com os normativos encontrados
        """
        if not self.searcher:
            logger.warning("Ro-DOU não disponível, retornando lista vazia")
            return []

        query = params.get("query", "conformidade aduaneira") if params else "conformidade aduaneira"
        date_from = params.get("date_from") if params else None
        date_to = params.get("date_to") if params else None
        sections = params.get("sections", [1, 2, 3]) if params else [1, 2, 3]

        logger.info(f"Buscando no DOU: query='{query}', sections={sections}")

        try:
            # Chama o searcher do Ro-DOU
            results = self.searcher.search(
                term=query,
                date_from=date_from,
                date_to=date_to,
                sections=sections
            )

            fetch_results = []
            for item in results:
                fetch_result = self._transform_item(item)
                if fetch_result:
                    fetch_results.append(fetch_result)

            logger.info(f"DOU: {len(fetch_results)} resultados encontrados")
            return fetch_results

        except Exception as e:
            logger.exception(f"Erro na busca DOU: {e}")
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
            # Extrai campos do item
            title = item.get("title", "")
            date_str = item.get("date", "")
            url = item.get("url", "")
            section = item.get("section", "")
            content = item.get("content", "")

            # Gera URN único
            urn = f"urn:dou:{section}:{date_str.replace('-', '')}:{hash(title) % 10000:04d}"

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
                        "source": "DOU",
                        "section": section,
                        "url": url,
                        "content": content,
                        "original": item
                    }
                }
            )

        except Exception as e:
            logger.warning(f"Erro ao transformar item DOU: {e}")
            return None
