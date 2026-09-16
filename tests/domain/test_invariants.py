"""
test_invariants.py — Testes property-based para InvariantsService
Usa hypothesis para gerar casos de teste automaticamente.
"""

import pytest
from hypothesis import given, strategies as st
from src.domain.services import InvariantsService


class TestInvariantsServiceQueries:
    """Testes para as queries Cypher dos invariantes."""

    def test_query_i1_existe(self):
        """Deve retornar query não vazia para I1."""
        query = InvariantsService.get_query_i1()
        assert query is not None
        assert len(query) > 0
        assert "MATCH" in query
        assert "ComponentTemporalVersion" in query

    def test_query_i2_existe(self):
        """Deve retornar query não vazia para I2."""
        query = InvariantsService.get_query_i2()
        assert query is not None
        assert len(query) > 0
        assert "MATCH" in query
        assert "CREATES" in query

    def test_query_i3_existe(self):
        """Deve retornar query não vazia para I3."""
        query = InvariantsService.get_query_i3()
        assert query is not None
        assert len(query) > 0
        assert "AGGREGATES" in query


class TestInvariantsServiceValidacao:
    """Testes para validação de resultados dos invariantes."""

    def test_todos_validos_zero_violacoes(self):
        """Quando todas violações são 0, todos_validos deve ser True."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=0,
            i2_violations=0,
            i3_violations=0
        )
        
        assert resultado["I1_cobertura_temporal"] == 0
        assert resultado["I2_causalidade_fechada"] == 0
        assert resultado["I3_agregacao"] == 0
        assert resultado["todos_validos"] is True

    def test_i1_com_violacao(self):
        """Quando I1 tem violações, todos_validos deve ser False."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=1,
            i2_violations=0,
            i3_violations=0
        )
        
        assert resultado["I1_cobertura_temporal"] == 1
        assert resultado["todos_validos"] is False

    def test_i2_com_violacao(self):
        """Quando I2 tem violações, todos_validos deve ser False."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=0,
            i2_violations=5,
            i3_violations=0
        )
        
        assert resultado["I2_causalidade_fechada"] == 5
        assert resultado["todos_validos"] is False

    def test_i3_com_violacao(self):
        """Quando I3 tem violações, todos_validos deve ser False."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=0,
            i2_violations=0,
            i3_violations=10
        )
        
        assert resultado["I3_agregacao"] == 10
        assert resultado["todos_validos"] is False

    def test_multiplas_violacoes(self):
        """Quando múltiplos invariantes têm violações."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=2,
            i2_violations=3,
            i3_violations=4
        )
        
        assert resultado["todos_validos"] is False
        assert resultado["I1_cobertura_temporal"] == 2
        assert resultado["I2_causalidade_fechada"] == 3
        assert resultado["I3_agregacao"] == 4

    @given(
        i1=st.integers(min_value=0, max_value=100),
        i2=st.integers(min_value=0, max_value=100),
        i3=st.integers(min_value=0, max_value=100)
    )
    def test_property_based_validacao(self, i1, i2, i3):
        """Property-based: validar estrutura do resultado para quaisquer valores."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=i1,
            i2_violations=i2,
            i3_violations=i3
        )
        
        # Estrutura sempre presente
        assert "I1_cobertura_temporal" in resultado
        assert "I2_causalidade_fechada" in resultado
        assert "I3_agregacao" in resultado
        assert "todos_validos" in resultado
        
        # Valores corretos
        assert resultado["I1_cobertura_temporal"] == i1
        assert resultado["I2_causalidade_fechada"] == i2
        assert resultado["I3_agregacao"] == i3
        
        # todos_validos só é True quando todos são 0
        esperado_valido = (i1 == 0 and i2 == 0 and i3 == 0)
        assert resultado["todos_validos"] == esperado_valido


class TestInvariantsServiceRelatorio:
    """Testes para formatação de relatório."""

    def test_relatorio_sem_violacoes(self):
        """Deve formatar relatório com todos invariantes válidos."""
        resultados = {
            "I1_cobertura_temporal": 0,
            "I2_causalidade_fechada": 0,
            "I3_agregacao": 0,
            "todos_validos": True,
        }
        
        relatorio = InvariantsService.formatar_relatorio(resultados)
        
        assert "✅" in relatorio
        assert "I1_cobertura_temporal: 0" in relatorio
        assert "I2_causalidade_fechada: 0" in relatorio
        assert "I3_agregacao: 0" in relatorio
        assert "Todos válidos: True" in relatorio

    def test_relatorio_com_violacoes(self):
        """Deve formatar relatório com violações."""
        resultados = {
            "I1_cobertura_temporal": 2,
            "I2_causalidade_fechada": 0,
            "I3_agregacao": 1,
            "todos_validos": False,
        }
        
        relatorio = InvariantsService.formatar_relatorio(resultados)
        
        assert "❌" in relatorio  # Pelo menos um ❌ para violações
        assert "I1_cobertura_temporal: 2" in relatorio
        assert "I3_agregacao: 1" in relatorio
        assert "Todos válidos: False" in relatorio

    def test_relatorio_formato_linhas(self):
        """Cada invariante deve estar em linha separada."""
        resultados = {
            "I1_cobertura_temporal": 0,
            "I2_causalidade_fechada": 0,
            "I3_agregacao": 0,
            "todos_validos": True,
        }
        
        relatorio = InvariantsService.formatar_relatorio(resultados)
        linhas = relatorio.split("\n")
        
        # Deve ter pelo menos 4 linhas (3 invariantes + 1 status geral)
        assert len(linhas) >= 4


class TestInvariantsServiceEdgeCases:
    """Testes para casos extremos."""

    def test_valores_negativos(self):
        """Valores negativos não devem ocorrer, mas o código deve lidar."""
        # Embora valores negativos não façam sentido, o serviço deve aceitar
        resultado = InvariantsService.validar_resultados(
            i1_violations=-1,
            i2_violations=0,
            i3_violations=0
        )
        
        # O sistema aceita o valor, mas todos_validos será False (-1 != 0)
        assert resultado["todos_validos"] is False

    def test_valores_muito_grandes(self):
        """Valores grandes devem ser tratados corretamente."""
        resultado = InvariantsService.validar_resultados(
            i1_violations=999999,
            i2_violations=888888,
            i3_violations=777777
        )
        
        assert resultado["I1_cobertura_temporal"] == 999999
        assert resultado["todos_validos"] is False
