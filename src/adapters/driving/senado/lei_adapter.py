"""
lei_adapter.py — Adapter para Leis Ordinárias e Complementares (Nível 3)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Leis (LEI, LC).
"""

from typing import Optional, Dict, Any
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida


class LeiAdapter:
    """
    Adapter específico para Leis Ordinárias e Complementares (Nível 3).
    
    Responsável por:
    - Extrair Leis Ordinárias (LEI) e Leis Complementares (LC) da API do Senado
    - Validar que o tipo é LEI ou LC
    - Retornar norma formatada para ingestão
    """

    def __init__(self, client: Optional[SenadoClient] = None):
        self.client = client or SenadoClient()

    def extrair_lei_ordinaria(self, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Extrai uma Lei Ordinária específica.
        
        Args:
            numero: Número da lei (ex: 10865)
            ano: Ano da lei (ex: 2004)
            
        Returns:
            NormaExtraida se encontrada, None caso contrário
        """
        norma = self.client.buscar_norma_completa("LEI", numero, ano)
        
        if norma and not self._validar_tipo_lei_ordinaria(norma.tipo):
            raise ValueError(
                f"Tipo inválido para Lei Ordinária: {norma.tipo}. "
                f"Esperado LEI."
            )
        
        return norma

    def extrair_lei_complementar(self, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Extrai uma Lei Complementar específica.
        
        Args:
            numero: Número da lei complementar (ex: 87)
            ano: Ano da lei complementar (ex: 1996)
            
        Returns:
            NormaExtraida se encontrada, None caso contrário
        """
        norma = self.client.buscar_norma_completa("LC", numero, ano)
        
        if norma and not self._validar_tipo_lei_complementar(norma.tipo):
            raise ValueError(
                f"Tipo inválido para Lei Complementar: {norma.tipo}. "
                f"Esperado LC."
            )
        
        return norma

    def _validar_tipo_lei_ordinaria(self, tipo: str) -> bool:
        """Valida se o tipo corresponde a uma Lei Ordinária."""
        return tipo.upper() == "LEI"

    def _validar_tipo_lei_complementar(self, tipo: str) -> bool:
        """Valida se o tipo corresponde a uma Lei Complementar."""
        return tipo.upper() == "LC"

    def extrair_com_validacao(
        self, 
        numero: int, 
        ano: int, 
        tipo: str = "LEI"
    ) -> Dict[str, Any]:
        """
        Extrai e valida uma Lei, retornando dict para ingestão.
        
        Args:
            numero: Número da lei
            ano: Ano da lei
            tipo: Tipo da lei ("LEI" ou "LC")
        
        Raises:
            ValueError: Se a norma não for encontrada ou tipo inválido
        """
        if tipo.upper() == "LC":
            norma = self.extrair_lei_complementar(numero, ano)
            tipo_norma = "LC"
            nivel = 3
        else:
            norma = self.extrair_lei_ordinaria(numero, ano)
            tipo_norma = "LEI"
            nivel = 3
        
        if norma is None:
            raise ValueError(f"{tipo} {numero}/{ano} não encontrada")
        
        return {
            "nivel": nivel,
            "tipo_norma": tipo_norma,
            "numero": norma.numero,
            "ano": norma.ano,
            "data_promulgacao": norma.data_promulgacao,
            "urn": norma.urn,
            "ementa": norma.ementa,
            "situacao": norma.situacao,
            "metadata": norma.to_dict(),
        }
