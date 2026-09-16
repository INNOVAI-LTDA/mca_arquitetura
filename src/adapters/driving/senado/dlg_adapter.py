"""
dlg_adapter.py — Adapter para Decretos Legislativos (Nível 2)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Decretos Legislativos.
"""

from typing import Optional, Dict, Any
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida


class DecretoLegislativoAdapter:
    """
    Adapter específico para Decretos Legislativos (Nível 2).
    
    Responsável por:
    - Extrair Decretos Legislativos da API do Senado
    - Validar que o tipo é DLG/DL
    - Retornar norma formatada para ingestão
    """

    def __init__(self, client: Optional[SenadoClient] = None):
        self.client = client or SenadoClient()

    def extrair(self, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Extrai um Decreto Legislativo específico.
        
        Args:
            numero: Número do decreto (ex: 135)
            ano: Ano do decreto (ex: 2019)
            
        Returns:
            NormaExtraida se encontrada, None caso contrário
        """
        # DLG é a sigla oficial, DL é a sigla comum
        norma = self.client.buscar_norma_completa("DLG", numero, ano)
        
        if norma is None:
            # Tenta com a sigla alternativa
            norma = self.client.buscar_norma_completa("DL", numero, ano)
        
        if norma and not self._validar_tipo_decreto_legislativo(norma.tipo):
            raise ValueError(
                f"Tipo inválido para Decreto Legislativo: {norma.tipo}. "
                f"Esperado DLG ou DL."
            )
        
        return norma

    def _validar_tipo_decreto_legislativo(self, tipo: str) -> bool:
        """Valida se o tipo corresponde a um Decreto Legislativo."""
        return tipo.upper() in ("DLG", "DL")

    def extrair_com_validacao(self, numero: int, ano: int) -> Dict[str, Any]:
        """
        Extrai e valida um Decreto Legislativo, retornando dict para ingestão.
        
        Raises:
            ValueError: Se a norma não for encontrada ou tipo inválido
        """
        norma = self.extrair(numero, ano)
        
        if norma is None:
            raise ValueError(f"Decreto Legislativo {numero}/{ano} não encontrado")
        
        return {
            "nivel": 2,
            "tipo_norma": "DLG",
            "numero": norma.numero,
            "ano": norma.ano,
            "data_promulgacao": norma.data_promulgacao,
            "urn": norma.urn,
            "ementa": norma.ementa,
            "situacao": norma.situacao,
            "metadata": norma.to_dict(),
        }
