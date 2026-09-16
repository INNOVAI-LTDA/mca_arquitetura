"""
dec_adapter.py — Adapter para Decretos (Nível 4)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Decretos.
"""

from typing import Optional, Dict, Any
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida


class DecretoAdapter:
    """
    Adapter específico para Decretos (Nível 4).
    
    Responsável por:
    - Extrair Decretos da API do Senado
    - Validar que o tipo é DEC
    - Retornar norma formatada para ingestão
    """

    def __init__(self, client: Optional[SenadoClient] = None):
        self.client = client or SenadoClient()

    def extrair(self, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Extrai um Decreto específico.
        
        Args:
            numero: Número do decreto (ex: 6759)
            ano: Ano do decreto (ex: 2009)
            
        Returns:
            NormaExtraida se encontrada, None caso contrário
        """
        norma = self.client.buscar_norma_completa("DEC", numero, ano)
        
        if norma and not self._validar_tipo_decreto(norma.tipo):
            raise ValueError(
                f"Tipo inválido para Decreto: {norma.tipo}. "
                f"Esperado DEC."
            )
        
        return norma

    def _validar_tipo_decreto(self, tipo: str) -> bool:
        """Valida se o tipo corresponde a um Decreto."""
        return tipo.upper() == "DEC"

    def extrair_com_validacao(self, numero: int, ano: int) -> Dict[str, Any]:
        """
        Extrai e valida um Decreto, retornando dict para ingestão.
        
        Raises:
            ValueError: Se a norma não for encontrada ou tipo inválido
        """
        norma = self.extrair(numero, ano)
        
        if norma is None:
            raise ValueError(f"Decreto {numero}/{ano} não encontrado")
        
        return {
            "nivel": 4,
            "tipo_norma": "DEC",
            "numero": norma.numero,
            "ano": norma.ano,
            "data_promulgacao": norma.data_promulgacao,
            "urn": norma.urn,
            "ementa": norma.ementa,
            "situacao": norma.situacao,
            "metadata": norma.to_dict(),
        }
