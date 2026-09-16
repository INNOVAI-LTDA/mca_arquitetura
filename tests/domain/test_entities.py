"""
test_entities.py — Testes unitários para entidades de domínio
"""

import pytest
from datetime import date
from src.domain.entities import (
    NormativeWork,
    ComponentTemporalVersion,
    LegislativeAction,
    FetchResult,
)


class TestNormativeWork:
    """Testes para a entidade NormativeWork."""

    def test_criar_norma_completa(self):
        """Deve criar uma norma com todos os atributos."""
        work = NormativeWork(
            urn="urn:lex:br:federal:lei:1990-04-09;8032",
            tipo="LEI",
            numero="8032",
            ano=1990,
            data_promulgacao="1990-04-09",
            ementa="Dispõe sobre políticas de comércio exterior",
            situacao="Vigente",
            codigo_senado=12345,
            fonte="API_Senado_Federal",
        )
        
        assert work.urn == "urn:lex:br:federal:lei:1990-04-09;8032"
        assert work.tipo == "LEI"
        assert work.numero == "8032"
        assert work.ano == 1990
        assert work.data_promulgacao == "1990-04-09"
        assert work.situacao == "Vigente"

    def test_valores_padrao(self):
        """Deve usar valores padrão corretamente."""
        work = NormativeWork(
            urn="urn:lex:br:federal:lei:2004-07-13;10865",
            tipo="LEI",
            numero="10865",
            ano=2004,
            data_promulgacao="2004-07-13",
            ementa="Institui PIS/COFINS-Importação",
            situacao="Vigente",
        )
        
        assert work.codigo_senado is None
        assert work.fonte == "API_Senado_Federal"
        assert work.observacao is None
        assert work.processo_origem == {}

    def test_to_dict(self):
        """Deve converter para dicionário corretamente."""
        work = NormativeWork(
            urn="urn:lex:br:federal:lei:1996-09-13;87",
            tipo="LC",
            numero="87",
            ano=1996,
            data_promulgacao="1996-09-13",
            ementa="Lei Kandir",
            situacao="Vigente",
        )
        
        result = work.to_dict()
        
        assert result["urn"] == "urn:lex:br:federal:lei:1996-09-13;87"
        assert result["tipo"] == "LC"
        assert result["numero"] == "87"
        assert result["ano"] == 1996
        assert result["fonte"] == "API_Senado_Federal"

    def test_from_dict(self):
        """Deve criar instância a partir de dicionário."""
        data = {
            "urn": "urn:lex:br:federal:decreto:2009-02-02;6759",
            "tipo": "DEC",
            "numero": "6759",
            "ano": 2009,
            "data_promulgacao": "2009-02-02",
            "ementa": "Regulamento Aduaneiro",
            "situacao": "Vigente",
            "codigo_senado": None,
            "fonte": "DOU",
        }
        
        work = NormativeWork.from_dict(data)
        
        assert work.urn == data["urn"]
        assert work.tipo == "DEC"
        assert work.numero == "6759"
        assert work.ano == 2009
        assert work.fonte == "DOU"

    def test_str_representation(self):
        """Deve formatar string corretamente."""
        work = NormativeWork(
            urn="urn:lex:br:federal:lei:1990-04-09;8032",
            tipo="LEI",
            numero="8032",
            ano=1990,
            data_promulgacao="1990-04-09",
            ementa="Teste",
            situacao="Vigente",
        )
        
        assert str(work) == "LEI 8032/1990 (1990-04-09)"


class TestComponentTemporalVersion:
    """Testes para a entidade ComponentTemporalVersion."""

    def test_criar_ctv_vigente(self):
        """Deve criar CTV vigente (sem data fim)."""
        ctv = ComponentTemporalVersion(
            urn="urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09",
            valid_start="1990-04-09",
            valid_end=None,
            nivel=0,
            componente_tipo="Norma_Completa",
        )
        
        assert ctv.valid_end is None
        assert ctv.vigente is True
        assert ctv.nivel == 0

    def test_criar_ctv_revogada(self):
        """Deve criar CTV com vigência encerrada."""
        ctv = ComponentTemporalVersion(
            urn="urn:lex:br:federal:lei:1990-04-09;8032@2000-01-01",
            valid_start="2000-01-01",
            valid_end="2010-12-31",
            nivel=0,
            componente_tipo="Norma_Completa",
        )
        
        assert ctv.valid_end == "2010-12-31"
        assert ctv.vigente is False

    def test_to_dict(self):
        """Deve converter para dicionário."""
        ctv = ComponentTemporalVersion(
            urn="urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09",
            valid_start="1990-04-09",
            valid_end=None,
            nivel=1,
            componente_tipo="Artigo",
            conteudo="Art. 1º Teste",
            work_urn="urn:lex:br:federal:lei:1990-04-09;8032",
        )
        
        result = ctv.to_dict()
        
        assert result["urn"] == "urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09"
        assert result["nivel"] == 1
        assert result["componente_tipo"] == "Artigo"
        assert result["conteudo"] == "Art. 1º Teste"

    def test_str_representation(self):
        """Deve formatar string corretamente."""
        ctv_vigente = ComponentTemporalVersion(
            urn="urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09",
            valid_start="1990-04-09",
            valid_end=None,
            nivel=0,
            componente_tipo="Norma_Completa",
        )
        
        assert str(ctv_vigente) == "CTV[Norma_Completa] 1990-04-09 → vigente"
        
        ctv_revogada = ComponentTemporalVersion(
            urn="urn:lex:br:federal:lei:1990-04-09;8032@2000-01-01",
            valid_start="2000-01-01",
            valid_end="2010-12-31",
            nivel=0,
            componente_tipo="Norma_Completa",
        )
        
        assert str(ctv_revogada) == "CTV[Norma_Completa] 2000-01-01 → 2010-12-31"


class TestLegislativeAction:
    """Testes para a entidade LegislativeAction."""

    def test_criar_action_criacao(self):
        """Deve criar ação de criação."""
        action = LegislativeAction(
            urn="urn:lex:br:federal:lei:1990-04-09;8032!action:criacao",
            action_type="CREATES",
            effective_date="1990-04-09",
            source_instrument="LEI 8032/1990",
            descricao="Criação da Lei 8032/1990",
        )
        
        assert action.action_type == "CREATES"
        assert action.target_ctvs == []

    def test_add_target_ctv(self):
        """Deve adicionar CTVs alvo sem duplicar."""
        action = LegislativeAction(
            urn="urn:lex:br:federal:lei:1990-04-09;8032!action:criacao",
            action_type="CREATES",
            effective_date="1990-04-09",
            source_instrument="LEI 8032/1990",
            descricao="Criação",
        )
        
        ctv_urn = "urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09"
        
        action.add_target_ctv(ctv_urn)
        assert len(action.target_ctvs) == 1
        assert ctv_urn in action.target_ctvs
        
        # Adicionar novamente não deve duplicar
        action.add_target_ctv(ctv_urn)
        assert len(action.target_ctvs) == 1

    def test_to_dict(self):
        """Deve converter para dicionário."""
        action = LegislativeAction(
            urn="urn:lex:br:federal:lei:1990-04-09;8032!action:criacao",
            action_type="CREATES",
            effective_date="1990-04-09",
            source_instrument="LEI 8032/1990",
            descricao="Criação",
            proveniencia_processo_id="12345",
            proveniencia_processo_identificacao="PL 1234/1989",
        )
        
        result = action.to_dict()
        
        assert result["urn"] == "urn:lex:br:federal:lei:1990-04-09;8032!action:criacao"
        assert result["proveniencia_processo_id"] == "12345"
        assert result["proveniencia_processo_identificacao"] == "PL 1234/1989"

    def test_str_representation(self):
        """Deve formatar string corretamente."""
        action = LegislativeAction(
            urn="urn:lex:br:federal:lei:1990-04-09;8032!action:criacao",
            action_type="CREATES",
            effective_date="1990-04-09",
            source_instrument="LEI 8032/1990",
            descricao="Criação",
        )
        
        assert str(action) == "CREATES: LEI 8032/1990 (1990-04-09)"


class TestFetchResult:
    """Testes para a classe FetchResult."""

    def test_sucesso(self):
        """Deve criar resultado de sucesso."""
        result = FetchResult(
            success=True,
            data={"key": "value"},
            metadata={"source": "senado"}
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_falha(self):
        """Deve criar resultado de falha."""
        result = FetchResult(
            success=False,
            error="Timeout na requisição",
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Timeout na requisição"

    def test_to_dict(self):
        """Deve converter para dicionário."""
        result = FetchResult(
            success=True,
            data={"norma": "LEI 8032/1990"},
            error=None,
            metadata={"retries": 2}
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["data"] == {"norma": "LEI 8032/1990"}
        assert d["error"] is None
        assert d["metadata"] == {"retries": 2}
