"""
dlg_adapter.py — Adapter para Decretos Legislativos (Nível 2)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Decretos Legislativos.
"""

from typing import Optional, Dict, Any, List
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida
from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult


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


class DlgAdapter(FetcherPort):
    """
    Wrapper que adapta DecretoLegislativoAdapter para a interface FetcherPort.
    """
    
    def __init__(self, client: Optional[SenadoClient] = None):
        self.adapter = DecretoLegislativoAdapter(client)
        self.client = client or SenadoClient()
    
    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca um Decreto Legislativo específico.
        
        Args:
            numero: Número do decreto
            ano: Ano do decreto
            
        Returns:
            FetchResult com o decreto encontrado
        """
        numero = kwargs.get("numero")
        ano = kwargs.get("ano")
        
        if not numero or not ano:
            return FetchResult(
                success=False,
                error="Parâmetros 'numero' e 'ano' são obrigatórios"
            )
        
        try:
            norma = self.adapter.extrair(numero, ano)
            if norma:
                return FetchResult(
                    success=True,
                    data={
                        "urn": norma.urn,
                        "title": norma.ementa or f"Decreto Legislativo {numero}/{ano}",
                        "date": norma.data_promulgacao,
                        "level": "L2",
                        "metadata": norma.to_dict()
                    }
                )
            else:
                return FetchResult(
                    success=False,
                    error=f"Decreto Legislativo {numero}/{ano} não encontrado"
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
            identifier: URN do decreto legislativo
            
        Returns:
            True se existir, False caso contrário
        """
        try:
            parts = identifier.split(":")
            if len(parts) >= 7:
                ano = parts[5]
                numero = parts[6]
                norma = self.adapter.extrair(int(numero), int(ano))
                return norma is not None
        except Exception:
            pass
        return False
    
    def fetch(self, params: Optional[Dict[str, Any]] = None) -> List[FetchResult]:
        """Executa fetch de Decretos Legislativos."""
        results = []
        from datetime import datetime
        current_year = datetime.now().year
        limit = params.get("limit", 10) if params else 10
        
        try:
            for year_offset in range(min(5, limit)):
                year = current_year - year_offset
                for num in range(1, min(3, limit // 5)):
                    try:
                        norma = self.adapter.extrair(num, year)
                        if norma:
                            results.append(FetchResult(
                                success=True,
                                data={
                                    "urn": norma.urn,
                                    "title": norma.ementa or f"Decreto Legislativo {num}/{year}",
                                    "date": norma.data_promulgacao,
                                    "level": "L2",
                                    "metadata": norma.to_dict()
                                }
                            ))
                    except Exception:
                        continue
        except Exception:
            pass
        
        return results
