"""
ports.py — Portas (Interfaces) do Domínio MCA
Arquitetura Hexagonal: Ports & Adapters

Este módulo define as interfaces (ports) que os adapters devem implementar.
O domínio NÃO depende de nenhum adapter concreto.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class FetchResult:
    """Resultado de uma operação de fetch."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class FetcherPort(ABC):
    """
    Porta para clientes de extração (Senado, NCM, Ro-DOU).
    Responsável por buscar dados de fontes externas.
    """

    @abstractmethod
    def buscar(self, **kwargs: Any) -> FetchResult:
        """Busca dados de uma fonte externa."""

    @abstractmethod
    def validar(self, identifier: str) -> bool:
        """Valida se um identificador existe na fonte."""


class IngestPort(ABC):
    """
    Porta para ingestão de dados no grafo (Neo4j).
    Responsável por persistir entidades no storage.
    """

    @abstractmethod
    def ingerir(self, entity: Any) -> bool:
        """Ingere uma entidade no storage."""

    @abstractmethod
    def ingerir_lote(self, entities: list[Any]) -> dict[str, int]:
        """Ingere um lote de entidades e retorna estatísticas."""

    @abstractmethod
    def validar_invariantes(self) -> dict[str, Any]:
        """Valida os invariantes I1, I2, I3 após ingestão."""


class URNPort(ABC):
    """
    Porta para geração e validação de URNs canônicos.
    Responsável por garantir conformidade com o padrão LexML.
    """

    @abstractmethod
    def gerar_urn(self, tipo: str, numero: str, data: str) -> str:
        """Gera um URN canônico conforme E1a."""

    @abstractmethod
    def validar_urn(self, urn: str) -> bool:
        """Valida se um URN segue o formato canônico."""
