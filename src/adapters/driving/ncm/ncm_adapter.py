"""
ncm_adapter.py — Adapter para Tabela NCM (Nível 5)
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a lógica específica para extração e parsing da NCM.
"""

from typing import Optional, Dict, Any, List
from src.adapters.driving.ncm.classif_client import ClassifClient, ItemNCM
from src.domain.ports import FetcherPort
from src.domain.entities import FetchResult


class NcmAdapter(FetcherPort):
    """
    Adapter para Tabela NCM (Nível 5).
    
    Responsável por:
    - Carregar tabela NCM via ClassifClient
    - Transformar itens NCM em FetchResult
    - Fornecer interface compatível com Pipeline
    """
    
    def __init__(self, client: Optional[ClassifClient] = None, json_path: Optional[str] = None):
        """
        Inicializa o adapter NCM.
        
        Args:
            client: Instância de ClassifClient (opcional)
            json_path: Caminho para arquivo JSON da NCM (se client não fornecido)
        """
        if client:
            self.client = client
        elif json_path:
            self.client = ClassifClient(json_path)
        else:
            self.client = ClassifClient()
    
    def buscar(self, **kwargs: Any) -> FetchResult:
        """
        Busca um item NCM específico.
        
        Args:
            codigo: Código NCM a buscar
            
        Returns:
            FetchResult com o item NCM encontrado
        """
        codigo = kwargs.get("codigo")
        
        if not codigo:
            return FetchResult(
                success=False,
                error="Parâmetro 'codigo' é obrigatório"
            )
        
        try:
            item = self.client.buscar_ncm(codigo)
            if item:
                return FetchResult(
                    success=True,
                    data={
                        "urn": item.urn,
                        "title": f"{item.tipo} {item.codigo_original}: {item.descricao}",
                        "date": item.data_inicio,
                        "level": "L5",
                        "metadata": item.to_dict()
                    }
                )
            else:
                return FetchResult(
                    success=False,
                    error=f"NCM {codigo} não encontrado"
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
            identifier: URN do item NCM
            
        Returns:
            True se existir, False caso contrário
        """
        try:
            # Parse do URN para extrair código
            # Formato esperado: urn:lex:br:ncm:...
            parts = identifier.split(":")
            if len(parts) >= 5:
                codigo = parts[-1]
                item = self.client.buscar_ncm(codigo)
                return item is not None
        except Exception:
            pass
        return False
    
    def fetch(self, params: Optional[Dict[str, Any]] = None) -> List[FetchResult]:
        """
        Executa fetch de itens NCM.
        
        Args:
            params: Parâmetros opcionais:
                - codigo: Buscar NCM específico
                - nivel: Filtrar por nível hierárquico
                - limite: Limitar número de resultados
                
        Returns:
            Lista de FetchResult com itens NCM
        """
        results = []
        
        try:
            # Busca específica por código
            if params and params.get("codigo"):
                codigo = params["codigo"]
                item = self.client.buscar_ncm(codigo)
                if item:
                    results.append(self._transform_item(item))
                return results
            
            # Busca por nível
            if params and params.get("nivel"):
                nivel = params["nivel"]
                items = self.client.buscar_por_nivel(nivel)
                limite = params.get("limite", len(items))
                for item in items[:limite]:
                    results.append(self._transform_item(item))
                return results
            
            # Busca geral (todos os níveis, limitado)
            limite = params.get("limite", 100) if params else 100
            stats = self.client.estatisticas()
            
            # Pega amostra de cada nível
            for nivel in [2, 4, 5, 6, 7, 8]:
                items = self.client.buscar_por_nivel(nivel)
                for item in items[:limite // 6]:
                    results.append(self._transform_item(item))
                    
        except Exception as e:
            # Se não há arquivo carregado, retorna lista vazia
            pass
        
        return results
    
    def _transform_item(self, item: ItemNCM) -> FetchResult:
        """
        Transforma ItemNCM em FetchResult.
        
        Args:
            item: ItemNCM estruturado
            
        Returns:
            FetchResult pronto para pipeline
        """
        return FetchResult(
            success=True,
            data={
                "urn": item.urn,
                "title": f"{item.tipo} {item.codigo_original}: {item.descricao}",
                "date": item.data_inicio,
                "level": "L5",
                "metadata": item.to_dict()
            }
        )
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da tabela NCM."""
        return self.client.estatisticas()
    
    def buscar_caminho(self, codigo: str) -> List[ItemNCM]:
        """Retorna caminho hierárquico de um NCM."""
        return self.client.buscar_caminho_hierarquico(codigo)
