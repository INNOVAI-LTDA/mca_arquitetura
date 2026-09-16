"""
services.py — Serviços de Domínio do MCA
Arquitetura Hexagonal: Domain Layer

Este módulo define os serviços de domínio que implementam lógica de negócio
pura, independente de adapters concretos.

Serviços principais:
- InvariantsService: Valida os invariantes I1, I2, I3 conforme E1a
"""

from typing import Any


class InvariantsService:
    """
    Serviço de domínio para validação dos invariantes de integridade.
    
    Conforme especificado em E1a, Seção 7:
    - I1: Cobertura Temporal Disjunta (sem sobreposição de vigência)
    - I2: Causalidade Fechada (todo CTV tem uma ação criadora)
    - I3: Agregação sem Redundância (filhos não podem ser mais recentes que pais)
    
    Este serviço contém APENAS a lógica de validação (queries Cypher).
    A execução das queries fica a cargo do adapter Neo4j.
    """

    # Query para validar I1: Cobertura Temporal Disjunta
    QUERY_I1 = """
        MATCH (c:NormativeComponent)-[:HAS_TEMPORAL_VERSION]->(tv1:ComponentTemporalVersion),
              (c)-[:HAS_TEMPORAL_VERSION]->(tv2:ComponentTemporalVersion)
        WHERE tv1 <> tv2
          AND tv1.valid_start < tv2.valid_end
          AND tv2.valid_start < tv1.valid_end
        RETURN count(*) AS violacoes
    """

    # Query para validar I2: Causalidade Fechada
    QUERY_I2 = """
        MATCH (ctv:ComponentTemporalVersion)
        WHERE NOT EXISTS { (ctv)<-[:CREATES]-(:LegislativeAction) }
          AND ctv.valid_start > date('1900-01-01')
        RETURN count(*) AS violacoes
    """

    # Query para validar I3: Agregação sem Redundância
    QUERY_I3 = """
        MATCH (tv_pai:ComponentTemporalVersion)-[:AGGREGATES]->(tv_filho:ComponentTemporalVersion)
        WHERE tv_filho.valid_start > tv_pai.valid_start
        RETURN count(*) AS violacoes
    """

    @classmethod
    def get_query_i1(cls) -> str:
        """Retorna a query Cypher para validar I1."""
        return cls.QUERY_I1

    @classmethod
    def get_query_i2(cls) -> str:
        """Retorna a query Cypher para validar I2."""
        return cls.QUERY_I2

    @classmethod
    def get_query_i3(cls) -> str:
        """Retorna a query Cypher para validar I3."""
        return cls.QUERY_I3

    @classmethod
    def validar_resultados(
        cls,
        i1_violations: int,
        i2_violations: int,
        i3_violations: int
    ) -> dict[str, Any]:
        """
        Valida os resultados das queries e retorna relatório estruturado.
        
        Args:
            i1_violations: Número de violações de I1
            i2_violations: Número de violações de I2
            i3_violations: Número de violações de I3
            
        Returns:
            Dicionário com status de cada invariante e status geral
        """
        return {
            "I1_cobertura_temporal": i1_violations,
            "I2_causalidade_fechada": i2_violations,
            "I3_agregacao": i3_violations,
            "todos_validos": (
                i1_violations == 0 and
                i2_violations == 0 and
                i3_violations == 0
            ),
        }

    @classmethod
    def formatar_relatorio(cls, resultados: dict[str, Any]) -> str:
        """
        Formata os resultados em um relatório legível.
        
        Args:
            resultados: Dicionário retornado por validar_resultados
            
        Returns:
            String formatada com status de cada invariante
        """
        linhas = []
        for nome, valor in resultados.items():
            if nome == "todos_validos":
                continue
            status = "✅" if valor == 0 else "❌"
            linhas.append(f"  {status} {nome}: {valor}")
        
        status_geral = "✅" if resultados["todos_validos"] else "❌"
        linhas.append(f"\n  {status_geral} Todos válidos: {resultados['todos_validos']}")
        
        return "\n".join(linhas)
