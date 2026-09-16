"""
test_senado_adapters.py — Testes para adapters do Senado (Níveis 1-4)

Critério de aceite: URNs gerados são idênticos aos do código legacy
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.adapters.driving.senado.senado_client import (
    SenadoClient,
    NormaExtraida,
    TIPO_URN_MAP,
    SIGLA_PARA_API,
)
from src.adapters.driving.senado.emc_adapter import EmendaConstitucionalAdapter
from src.adapters.driving.senado.dlg_adapter import DecretoLegislativoAdapter
from src.adapters.driving.senado.lei_adapter import LeiAdapter
from src.adapters.driving.senado.dec_adapter import DecretoAdapter


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_response_emc():
    """Mock de resposta para Emenda Constitucional."""
    return {
        "DetalheDocumento": {
            "documentos": {
                "documento": [
                    {
                        "id": 12345,
                        "identificacao": {
                            "tipo": "EMC",
                            "numero": 33,
                            "dataassinatura": "01/01/2001",
                        },
                        "ementa": "Altera o sistema tributário nacional",
                        "situacao": "Em vigor",
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_response_dlg():
    """Mock de resposta para Decreto Legislativo."""
    return {
        "DetalheDocumento": {
            "documentos": {
                "documento": [
                    {
                        "id": 67890,
                        "identificacao": {
                            "tipo": "DLG",
                            "numero": 135,
                            "dataassinatura": "15/05/2019",
                        },
                        "ementa": "Aprova acordo internacional",
                        "situacao": "Em vigor",
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_response_lei():
    """Mock de resposta para Lei Ordinária."""
    return {
        "DetalheDocumento": {
            "documentos": {
                "documento": [
                    {
                        "id": 11111,
                        "identificacao": {
                            "tipo": "LEI",
                            "numero": 10865,
                            "dataassinatura": "30/04/2004",
                        },
                        "ementa": "Institui contribuições sociais",
                        "situacao": "Em vigor",
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_response_lc():
    """Mock de resposta para Lei Complementar."""
    return {
        "DetalheDocumento": {
            "documentos": {
                "documento": [
                    {
                        "id": 22222,
                        "identificacao": {
                            "tipo": "LC",
                            "numero": 87,
                            "dataassinatura": "13/09/1996",
                        },
                        "ementa": "Lei Kandir - ICMS",
                        "situacao": "Em vigor",
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_response_dec():
    """Mock de resposta para Decreto."""
    return {
        "DetalheDocumento": {
            "documentos": {
                "documento": [
                    {
                        "id": 33333,
                        "identificacao": {
                            "tipo": "DEC",
                            "numero": 6759,
                            "dataassinatura": "05/02/2009",
                        },
                        "ementa": "Regulamento Aduaneiro",
                        "situacao": "Em vigor",
                    }
                ]
            }
        }
    }


@pytest.fixture
def senado_client():
    """Cliente do Senado com configuração de teste."""
    return SenadoClient(timeout=5, max_retries=1)


# =============================================================================
# TESTES DO SENADO CLIENT
# =============================================================================

class TestSenadoClient:
    """Testes unitários para SenadoClient."""

    def test_converter_sigla_ec_para_emc(self, senado_client):
        """Testa conversão de EC (comum) para EMC (oficial)."""
        assert senado_client._converter_sigla("EC") == "EMC"
        assert senado_client._converter_sigla("ec") == "EMC"
        assert senado_client._converter_sigla("Ec") == "EMC"

    def test_converter_sigla_dl_para_dlg(self, senado_client):
        """Testa conversão de DL (comum) para DLG (oficial)."""
        assert senado_client._converter_sigla("DL") == "DLG"
        assert senado_client._converter_sigla("dl") == "DLG"

    def test_converter_sigla_ja_oficial(self, senado_client):
        """Testa que siglas já oficiais permanecem inalteradas."""
        assert senado_client._converter_sigla("EMC") == "EMC"
        assert senado_client._converter_sigla("DLG") == "DLG"
        assert senado_client._converter_sigla("DEC") == "DEC"
        assert senado_client._converter_sigla("LEI") == "LEI"
        assert senado_client._converter_sigla("LC") == "LC"

    def test_gerar_urn_emc(self, senado_client):
        """Testa geração de URN para Emenda Constitucional."""
        urn = senado_client._gerar_urn("EMC", "33", "2001-01-01")
        expected = "urn:lex:br:federal:constituicao:emenda:2001-01-01;33"
        assert urn == expected

    def test_gerar_urn_dlg(self, senado_client):
        """Testa geração de URN para Decreto Legislativo."""
        urn = senado_client._gerar_urn("DLG", "135", "2019-05-15")
        expected = "urn:lex:br:federal:decreto.legislativo:2019-05-15;135"
        assert urn == expected

    def test_gerar_urn_com_sigla_comum(self, senado_client):
        """Testa que URN é gerado corretamente mesmo com sigla comum."""
        # EC deve ser convertido internamente para EMC
        urn = senado_client._gerar_urn("EC", "33", "2001-01-01")
        expected = "urn:lex:br:federal:constituicao:emenda:2001-01-01;33"
        assert urn == expected

    @patch.object(SenadoClient, '_request')
    def test_buscar_norma_emc_sucesso(self, mock_request, mock_response_emc, senado_client):
        """Testa busca de Emenda Constitucional com sucesso."""
        mock_request.return_value = mock_response_emc
        
        norma = senado_client.buscar_norma("EMC", 33, 2001)
        
        assert norma is not None
        assert norma.tipo == "EMC"
        assert norma.numero == "33"
        assert norma.ano == 2001
        assert norma.data_promulgacao == "2001-01-01"
        assert "Altera o sistema tributário" in norma.ementa
        assert norma.codigo_senado == 12345
        
        # Verifica URN gerado
        expected_urn = "urn:lex:br:federal:constituicao:emenda:2001-01-01;33"
        assert norma.urn == expected_urn

    @patch.object(SenadoClient, '_request')
    def test_buscar_norma_nao_encontrada(self, mock_request, senado_client):
        """Testa busca de norma não encontrada."""
        mock_request.return_value = None
        
        norma = senado_client.buscar_norma("EMC", 999, 1900)
        
        assert norma is None

    @patch.object(SenadoClient, '_request')
    def test_buscar_norma_com_data_formato_alternativo(self, mock_request, senado_client):
        """Testa parsing de data em formato ISO direto."""
        response = {
            "DetalheDocumento": {
                "documentos": {
                    "documento": [{
                        "id": 1,
                        "identificacao": {
                            "tipo": "LEI",
                            "numero": 1,
                            "dataassinatura": "2001-01-15",
                        },
                        "ementa": "Teste",
                        "situacao": "Em vigor",
                    }]
                }
            }
        }
        mock_request.return_value = response
        
        norma = senado_client.buscar_norma("LEI", 1, 2001)
        
        assert norma is not None
        assert norma.data_promulgacao == "2001-01-15"


# =============================================================================
# TESTES DOS ADAPTERS ESPECÍFICOS
# =============================================================================

class TestEmendaConstitucionalAdapter:
    """Testes para EmendaConstitucionalAdapter (Nível 1)."""

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_emc_sucesso(self, mock_buscar, mock_response_emc):
        """Testa extração de Emenda Constitucional com sucesso."""
        mock_buscar.return_value = NormaExtraida(
            tipo="EMC",
            numero="33",
            ano=2001,
            data_promulgacao="2001-01-01",
            ementa="Altera o sistema tributário",
            situacao="Em vigor",
            codigo_senado=12345,
            urn="urn:lex:br:federal:constituicao:emenda:2001-01-01;33"
        )
        
        adapter = EmendaConstitucionalAdapter()
        resultado = adapter.extrair_com_validacao(33, 2001)
        
        assert resultado["nivel"] == 1
        assert resultado["tipo_norma"] == "EMC"
        assert resultado["numero"] == "33"
        assert resultado["ano"] == 2001
        assert "tributário" in resultado["ementa"]

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_emc_tipo_invalido(self, mock_buscar):
        """Testa que adapter rejeita tipo inválido para EMC."""
        mock_buscar.return_value = NormaExtraida(
            tipo="LEI",  # Tipo errado!
            numero="33",
            ano=2001,
            data_promulgacao="2001-01-01",
            ementa="Teste",
            situacao="Em vigor",
            codigo_senado=1,
            urn="urn:teste"
        )
        
        adapter = EmendaConstitucionalAdapter()
        
        with pytest.raises(ValueError, match="Tipo inválido"):
            adapter.extrair(33, 2001)


class TestDecretoLegislativoAdapter:
    """Testes para DecretoLegislativoAdapter (Nível 2)."""

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_dlg_sucesso(self, mock_buscar):
        """Testa extração de Decreto Legislativo com sucesso."""
        mock_buscar.return_value = NormaExtraida(
            tipo="DLG",
            numero="135",
            ano=2019,
            data_promulgacao="2019-05-15",
            ementa="Aprova acordo internacional",
            situacao="Em vigor",
            codigo_senado=67890,
            urn="urn:lex:br:federal:decreto.legislativo:2019-05-15;135"
        )
        
        adapter = DecretoLegislativoAdapter()
        resultado = adapter.extrair_com_validacao(135, 2019)
        
        assert resultado["nivel"] == 2
        assert resultado["tipo_norma"] == "DLG"
        assert resultado["numero"] == "135"


class TestLeiAdapter:
    """Testes para LeiAdapter (Nível 3)."""

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_lei_ordinaria(self, mock_buscar):
        """Testa extração de Lei Ordinária."""
        mock_buscar.return_value = NormaExtraida(
            tipo="LEI",
            numero="10865",
            ano=2004,
            data_promulgacao="2004-04-30",
            ementa="Institui contribuições",
            situacao="Em vigor",
            codigo_senado=11111,
            urn="urn:lex:br:federal:lei:2004-04-30;10865"
        )
        
        adapter = LeiAdapter()
        resultado = adapter.extrair_com_validacao(10865, 2004, tipo="LEI")
        
        assert resultado["nivel"] == 3
        assert resultado["tipo_norma"] == "LEI"

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_lei_complementar(self, mock_buscar):
        """Testa extração de Lei Complementar."""
        mock_buscar.return_value = NormaExtraida(
            tipo="LC",
            numero="87",
            ano=1996,
            data_promulgacao="1996-09-13",
            ementa="Lei Kandir",
            situacao="Em vigor",
            codigo_senado=22222,
            urn="urn:lex:br:federal:lei.complementar:1996-09-13;87"
        )
        
        adapter = LeiAdapter()
        resultado = adapter.extrair_com_validacao(87, 1996, tipo="LC")
        
        assert resultado["nivel"] == 3
        assert resultado["tipo_norma"] == "LC"


class TestDecretoAdapter:
    """Testes para DecretoAdapter (Nível 4)."""

    @patch.object(SenadoClient, 'buscar_norma_completa')
    def test_extrair_decreto_sucesso(self, mock_buscar):
        """Testa extração de Decreto com sucesso."""
        mock_buscar.return_value = NormaExtraida(
            tipo="DEC",
            numero="6759",
            ano=2009,
            data_promulgacao="2009-02-05",
            ementa="Regulamento Aduaneiro",
            situacao="Em vigor",
            codigo_senado=33333,
            urn="urn:lex:br:federal:decreto:2009-02-05;6759"
        )
        
        adapter = DecretoAdapter()
        resultado = adapter.extrair_com_validacao(6759, 2009)
        
        assert resultado["nivel"] == 4
        assert resultado["tipo_norma"] == "DEC"
        assert resultado["numero"] == "6759"


# =============================================================================
# TESTES DE INTEGRIDADE DE URN (CRITÉRIO DE ACEITE)
# =============================================================================

class TestURNIntegrity:
    """
    Testes de integridade de URN.
    
    Critério de aceite: URNs gerados devem ser IDÊNTICOS aos do código legacy.
    """

    def test_urn_map_completo(self):
        """Verifica mapeamento completo de tipos para URN."""
        expected_mapping = {
            "EMC": "constituicao:emenda",
            "DLG": "decreto.legislativo",
            "DEC": "decreto",
            "LEI": "lei",
            "LC": "lei.complementar",
        }
        
        for tipo, segmento in expected_mapping.items():
            assert tipo in TIPO_URN_MAP
            assert TIPO_URN_MAP[tipo] == segmento

    def test_sigla_para_api_completo(self):
        """Verifica mapeamento reverso completo."""
        expected_mapping = {
            "EC": "EMC",
            "DL": "DLG",
            "DEC": "DEC",
            "LEI": "LEI",
            "LC": "LC",
        }
        
        for comum, oficial in expected_mapping.items():
            assert comum in SIGLA_PARA_API
            assert SIGLA_PARA_API[comum] == oficial

    @pytest.mark.parametrize("tipo,num,ano,expected_urn", [
        ("EMC", 33, 2001, "urn:lex:br:federal:constituicao:emenda:2001-01-01;33"),
        ("DLG", 135, 2019, "urn:lex:br:federal:decreto.legislativo:2019-05-15;135"),
        ("DEC", 6759, 2009, "urn:lex:br:federal:decreto:2009-02-05;6759"),
        ("LEI", 10865, 2004, "urn:lex:br:federal:lei:2004-04-30;10865"),
        ("LC", 87, 1996, "urn:lex:br:federal:lei.complementar:1996-09-13;87"),
    ])
    def test_urns_legacy_equivalent(self, tipo, num, ano, expected_urn):
        """
        Verifica que URNs gerados são equivalentes ao formato legacy.
        
        Este teste valida o critério de aceite principal da Tarefa 2.
        """
        client = SenadoClient()
        # Simula data fixa para teste determinístico
        data_fixa = f"{ano}-01-01" if num != 33 else "2001-01-01"
        
        # Ajusta datas específicas para cada caso de teste
        if num == 135:
            data_fixa = "2019-05-15"
        elif num == 6759:
            data_fixa = "2009-02-05"
        elif num == 10865:
            data_fixa = "2004-04-30"
        elif num == 87:
            data_fixa = "1996-09-13"
        
        urn = client._gerar_urn(tipo, str(num), data_fixa)
        assert urn == expected_urn, f"URN divergente para {tipo} {num}/{ano}"
