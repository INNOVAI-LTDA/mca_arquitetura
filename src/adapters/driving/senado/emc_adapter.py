"""
emc_adapter.py — Adapter para Emendas Constitucionais (Nível 1)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Emendas Constitucionais.
"""

from typing import Optional, Dict, Any
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida


class EmendaConstitucionalAdapter:
    """
    Adapter específico para Emendas Constitucionais (Nível 1).
    
    Responsável por:
    - Extrair Emendas Constitucionais da API do Senado
    - Validar que o tipo é EMC/EC
    - Retornar norma formatada para ingestão
    """

    def __init__(self, client: Optional[SenadoClient] = None):
        self.client = client or SenadoClient()

    def extrair(self, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Extrai uma Emenda Constitucional específica.
        
        Args:
            numero: Número da emenda (ex: 33)
            ano: Ano da emenda (ex: 2001)
            
        Returns:
            NormaExtraida se encontrada, None caso contrário
        """
        # EMC é a sigla oficial, EC é a sigla comum
        norma = self.client.buscar_norma_completa("EMC", numero, ano)
        
        if norma is None:
            # Tenta com a sigla alternativa
            norma = self.client.buscar_norma_completa("EC", numero, ano)
        
        if norma and not self._validar_tipo_emenda(norma.tipo):
            raise ValueError(
                f"Tipo inválido para Emenda Constitucional: {norma.tipo}. "
                f"Esperado EMC ou EC."
            )
        
        return norma

    def _validar_tipo_emenda(self, tipo: str) -> bool:
        """Valida se o tipo corresponde a uma Emenda Constitucional."""
        return tipo.upper() in ("EMC", "EC")

    def extrair_com_validacao(self, numero: int, ano: int) -> Dict[str, Any]:
        """
        Extrai e valida uma Emenda Constitucional, retornando dict para ingestão.
        
        Raises:
            ValueError: Se a norma não for encontrada ou tipo inválido
        """
        norma = self.extrair(numero, ano)
        
        if norma is None:
            raise ValueError(f"Emenda Constitucional {numero}/{ano} não encontrada")
        
        return {
            "nivel": 1,
            "tipo_norma": "EMC",
            "numero": norma.numero,
            "ano": norma.ano,
            "data_promulgacao": norma.data_promulgacao,
            "urn": norma.urn,
            "ementa": norma.ementa,
            "situacao": norma.situacao,
            "metadata": norma.to_dict(),
        }
