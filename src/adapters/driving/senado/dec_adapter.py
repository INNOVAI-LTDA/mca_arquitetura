"""
dec_adapter.py — Adapter para Decretos (Nível 4)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Decretos.
"""

from typing import Optional, Dict, Any, List
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida
from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult


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


class DecAdapter(FetcherPort):
    """
    Wrapper que adapta DecretoAdapter para a interface FetcherPort.
    """
    
    def __init__(self, client: Optional[SenadoClient] = None):
        self.adapter = DecretoAdapter(client)
        self.client = client or SenadoClient()
    
    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca um Decreto específico.
        
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
                        "title": norma.ementa or f"Decreto {numero}/{ano}",
                        "date": norma.data_promulgacao,
                        "level": "L4",
                        "metadata": norma.to_dict()
                    }
                )
            else:
                return FetchResult(
                    success=False,
                    error=f"Decreto {numero}/{ano} não encontrado"
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
            identifier: URN do decreto
            
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
        """Executa fetch de Decretos."""
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
                                    "title": norma.ementa or f"Decreto {num}/{year}",
                                    "date": norma.data_promulgacao,
                                    "level": "L4",
                                    "metadata": norma.to_dict()
                                }
                            ))
                    except Exception:
                        continue
        except Exception:
            pass
        
        return results
