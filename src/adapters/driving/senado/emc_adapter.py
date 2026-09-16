"""
emc_adapter.py — Adapter para Emendas Constitucionais (Nível 1)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração de Emendas Constitucionais.
"""

from typing import Optional, Dict, Any, List
from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida
from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult


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


class EmcAdapter(FetcherPort):
    """
    Wrapper que adapta EmendaConstitucionalAdapter para a interface FetcherPort.
    
    Permite que o adapter seja usado pelo Orchestrator/Pipeline.
    """
    
    def __init__(self, client: Optional[SenadoClient] = None):
        self.adapter = EmendaConstitucionalAdapter(client)
        self.client = client or SenadoClient()
    
    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca uma Emenda Constitucional específica.
        
        Args:
            numero: Número da emenda
            ano: Ano da emenda
            
        Returns:
            FetchResult com a emenda encontrada
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
                        "title": norma.ementa or f"Emenda Constitucional {numero}/{ano}",
                        "date": norma.data_promulgacao,
                        "level": "L1",
                        "metadata": norma.to_dict()
                    }
                )
            else:
                return FetchResult(
                    success=False,
                    error=f"Emenda Constitucional {numero}/{ano} não encontrada"
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
            identifier: URN da emenda constitucional
            
        Returns:
            True se existir, False caso contrário
        """
        # Implementação simplificada - tenta buscar pela urn
        # Em produção, usaria a API do Senado para validar existência
        try:
            # Parse do URN para extrair numero e ano
            # Formato: urn:lex:br:senado:emenda.constitucional:2001::33
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
        """
        Executa fetch de Emendas Constitucionais.
        
        Args:
            params: Parâmetros opcionais (limit, year_range, etc.)
            
        Returns:
            Lista de FetchResult com as emendas encontradas
        """
        # Implementação simplificada para demonstração
        # Em produção, usaria os parâmetros para buscar múltiplas emendas
        results = []
        
        # Exemplo: busca emendas recentes (últimos 5 anos)
        from datetime import datetime
        current_year = datetime.now().year
        
        limit = params.get("limit", 10) if params else 10
        
        # Nota: Esta é uma implementação simplificada
        # O código legacy teria a lógica completa de paginação
        try:
            # Tenta buscar algumas emendas de exemplo
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
                                    "title": norma.ementa or f"Emenda Constitucional {num}/{year}",
                                    "date": norma.data_promulgacao,
                                    "level": "L1",
                                    "metadata": norma.to_dict()
                                }
                            ))
                    except Exception:
                        continue
        except Exception:
            pass
        
        return results
