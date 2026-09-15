"""
senado_client.py — Cliente Python para a API de Dados Abertos do Senado Federal
Projeto: Motor de Conformidade Aduaneira (MCA) — PIPE FAPESP Fase 1
Relatório Técnico: RT-001

Versão corrigida com siglas oficiais da API do Senado:
- Emenda Constitucional: EMC (não EC)
- Decreto Legislativo: DLG (não DL)
- Decreto: DEC (correto)
"""

import requests
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES E MAPEAMENTOS
# =============================================================================

BASE_URL = "https://legis.senado.leg.br/dadosabertos"

# Mapeamento de tipo de norma → segmento URN (conforme E1a, Seção 3.2)
# ATENÇÃO: As siglas aqui são as SIGLAS OFICIAIS da API do Senado
TIPO_URN_MAP = {
    "EMC": "constituicao:emenda",      # Emenda Constitucional
    "DLG": "decreto.legislativo",      # Decreto Legislativo
    "DEC": "decreto",                  # Decreto
    "LEI": "lei",                      # Lei Ordinária
    "LC":  "lei.complementar",         # Lei Complementar
}

# Mapeamento reverso: sigla comum → sigla oficial da API
SIGLA_PARA_API = {
    "EC":  "EMC",   # Emenda Constitucional
    "DL":  "DLG",   # Decreto Legislativo
    "DEC": "DEC",   # Decreto
    "LEI": "LEI",   # Lei Ordinária
    "LC":  "LC",    # Lei Complementar
}

# Rate limit da API: 10 requisições/segundo (margem de segurança)
RATE_LIMIT_DELAY = 0.15
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_RETRIES = 3


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NormaExtraida:
    """Estrutura de dados representando uma norma extraída da API."""
    tipo: str
    numero: str
    ano: int
    data_promulgacao: str
    ementa: str
    situacao: str
    codigo_senado: Optional[int]
    urn: str
    observacao: Optional[str] = None
    processo_origem: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "numero": self.numero,
            "ano": self.ano,
            "data_promulgacao": self.data_promulgacao,
            "ementa": self.ementa,
            "situacao": self.situacao,
            "codigo_senado": self.codigo_senado,
            "urn": self.urn,
            "observacao": self.observacao,
            "processo_origem": self.processo_origem,
        }

    def __str__(self) -> str:
        return f"{self.tipo} {self.numero}/{self.ano} ({self.data_promulgacao})"


# =============================================================================
# CLIENTE DA API DO SENADO
# =============================================================================

class SenadoClient:
    """Cliente HTTP para a API de Dados Abertos do Senado Federal."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES):
        self.base_url = BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "MCA-Project/1.0 (PIPE-FAPESP; diego@daleship.com.br)"
        })
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Respeita o rate limit de 10 req/s da API."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Executa uma requisição HTTP com retry e rate limiting."""
        self._rate_limit()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limit atingido. Aguardando {wait}s...")
                    time.sleep(wait)
                    continue

                if response.status_code == 404:
                    logger.warning(f"Recurso não encontrado: {url}")
                    return None

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.error(f"Timeout na tentativa {attempt}/{self.max_retries}: {url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na tentativa {attempt}/{self.max_retries}: {e}")

            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        return None

    def _converter_sigla(self, tipo: str) -> str:
        """
        Converte sigla comum (EC, DL) para sigla oficial da API (EMC, DLG).
        Se a sigla já estiver no formato oficial, retorna como está.
        """
        tipo_upper = tipo.upper()
        return SIGLA_PARA_API.get(tipo_upper, tipo_upper)

    def _gerar_urn(self, tipo: str, numero: str, data: str) -> str:
        """Gera URN canônico conforme padrão E1a."""
        # Converte para sigla oficial se necessário
        tipo_oficial = self._converter_sigla(tipo)
        segmento = TIPO_URN_MAP.get(tipo_oficial, "norma")
        return f"urn:lex:br:federal:{segmento}:{data};{numero}"

    def _extrair_norma_do_json(self, data: Dict) -> Optional[Dict]:
        """Extrai os dados da norma da estrutura JSON retornada pela API."""
        if not data:
            return None

        # Caminho 1: Estrutura padrão de DetalheDocumento
        documentos = (
            data.get("DetalheDocumento", {})
                .get("documentos", {})
                .get("documento", [])
        )

        # Caminho 2: Fallback para outras estruturas possíveis
        if not documentos:
            documentos = (
                data.get("NormaJuridica", [])
                or data.get("documento", [])
                or [data.get("documento", data)]
            )

        if isinstance(documentos, dict):
            documentos = [documentos]

        if not documentos:
            return None

        return documentos[0]

    def buscar_norma(self, tipo: str, numero: int, ano: int) -> Optional[NormaExtraida]:
        """
        Busca uma norma específica por tipo/número/ano.
        Endpoint: /legislacao/{tipo}/{numero}/{ano}.json
        
        Aceita tanto siglas comuns (EC, DL) quanto oficiais (EMC, DLG).
        """
        # Converte sigla para formato oficial da API
        tipo_api = self._converter_sigla(tipo)
        
        url = f"{self.base_url}/legislacao/{tipo_api}/{numero}/{ano}.json"
        data = self._request(url)

        if not data:
            logger.error(f"Norma não encontrada: {tipo_api} {numero}/{ano}")
            return None

        doc = self._extrair_norma_do_json(data)
        if not doc:
            logger.error(f"Estrutura JSON inesperada para {tipo_api} {numero}/{ano}")
            return None

        # Extração de campos com fallback
        identificacao = doc.get("identificacao", {})
        
        tipo_norma = identificacao.get("tipo", tipo_api)
        numero_norma = str(identificacao.get("numero", numero))
        ementa = doc.get("ementa", "") or ""
        codigo = doc.get("id")
        
        # Conversão de data: "13/09/1996" -> "1996-09-13"
        data_str_raw = str(identificacao.get("dataassinatura", doc.get("data", ""))).strip()
        if data_str_raw and len(data_str_raw) >= 10:
            try:
                data_obj = datetime.strptime(data_str_raw[:10], "%d/%m/%Y")
                data_promulgacao = data_obj.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    data_obj = datetime.strptime(data_str_raw[:10], "%Y-%m-%d")
                    data_promulgacao = data_obj.strftime("%Y-%m-%d")
                except ValueError:
                    data_promulgacao = f"{ano}-01-01"
                    logger.warning(f"Formato de data inesperado '{data_str_raw}'. Usando fallback: {data_promulgacao}")
        else:
            data_promulgacao = f"{ano}-01-01"

        # Gera URN canônico
        urn = self._gerar_urn(tipo, numero_norma, data_promulgacao)

        return NormaExtraida(
            tipo=tipo_norma,
            numero=numero_norma,
            ano=ano,
            data_promulgacao=data_promulgacao,
            ementa=ementa,
            situacao=doc.get("situacao", "Desconhecida"),
            codigo_senado=codigo,
            urn=urn,
            observacao=identificacao.get("normaNome") or identificacao.get("apelido"),
        )

    def validar_urn(self, urn: str) -> Optional[Dict]:
        """Valida se um URN canônico existe no acervo oficial (normas.leg.br)."""
        url = f"{self.base_url}/legislacao/urn.json"
        params = {"urn": urn}
        data = self._request(url, params=params)
        
        if data:
            logger.info(f"URN validado com sucesso: {urn}")
        else:
            logger.warning(f"URN não encontrado no acervo oficial: {urn}")
        
        return data

    def buscar_processo_origem(self, tipo_norma: str, numero_norma: str, ano_norma: int) -> Optional[Dict]:
        """Rastreia o processo legislativo que originou uma norma."""
        url = f"{self.base_url}/processo.json"
        params = {
            "tipoNorma": tipo_norma,
            "numeroNorma": numero_norma,
            "anoNorma": ano_norma,
        }
        data = self._request(url, params=params)

        if not data:
            return None

        # O endpoint /processo retorna uma lista direta de processos
        if isinstance(data, list):
            processos = data
        elif isinstance(data, dict):
            processos = (
                data.get("processos", {}).get("processo", [])
                or data.get("processo", [])
            )
            if isinstance(processos, dict):
                processos = [processos]
        else:
            processos = []

        if not processos:
            logger.info(f"Nenhum processo encontrado para {tipo_norma} {numero_norma}/{ano_norma}")
            return None

        processo = processos[0]
        logger.info(f"Processo de origem encontrado: {processo.get('identificacao', 'N/A')}")
        return processo

    def buscar_norma_completa(self, tipo: str, numero: int, ano: int) -> Optional[NormaExtraida]:
        """Busca norma completa com metadados de proveniência."""
        norma = self.buscar_norma(tipo, numero, ano)
        if not norma:
            return None

        # Converte tipo para formato oficial da API antes de buscar processo
        tipo_api = self._converter_sigla(tipo)
        
        # Tenta rastrear a proveniência
        processo = self.buscar_processo_origem(tipo_api, norma.numero, ano)
        if processo:
            norma.processo_origem = {
                "id": processo.get("id"),
                "identificacao": processo.get("identificacao"),
                "autoria": processo.get("autoria"),
                "data_apresentacao": processo.get("dataApresentacao"),
                "situacao": processo.get("situacaoAtual"),
            }

        return norma


# =============================================================================
# SCRIPT DE TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DE INTEGRAÇÃO — API do Senado Federal (MCA)")
    print("Versão com siglas oficiais corrigidas (EMC, DLG, DEC)")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    client = SenadoClient()

    # Casos de teste representativos dos Níveis 1, 2 e 3
    # Agora usando as siglas corretas: EMC (Emenda), DLG (Decreto Legislativo)
    casos = [
        {"nivel": 1, "tipo": "EMC", "numero": 33,    "ano": 2001, "desc": "EMC 33/2001 (ICMS Interestadual)"},
        {"nivel": 2, "tipo": "DLG", "numero": 135,   "ano": 2019, "desc": "DLG 135/2019 (Acordo OMC)"},
        {"nivel": 3, "tipo": "LC",  "numero": 87,    "ano": 1996, "desc": "LC 87/1996 (Lei Kandir)"},
        {"nivel": 3, "tipo": "LEI", "numero": 10865, "ano": 2004, "desc": "Lei 10.865/2004 (PIS/COFINS)"},
        {"nivel": 4, "tipo": "DEC", "numero": 6759, "ano": 2009, "desc": "Decreto 6.759/2009 (Regulamento Aduaneiro)"}
    ]

    resultados = []
    for caso in casos:
        print(f"\n[TESTE] Nível {caso['nivel']}: {caso['desc']}")
        norma = client.buscar_norma_completa(caso["tipo"], caso["numero"], caso["ano"])

        if norma:
            print(f"  ✅ SUCESSO:")
            print(f"     URN              : {norma.urn}")
            print(f"     Data Promulgação : {norma.data_promulgacao}")
            print(f"     Situação         : {norma.situacao}")
            print(f"     Ementa           : {norma.ementa[:80]}...")
            if norma.processo_origem:
                print(f"     Processo Origem  : {norma.processo_origem.get('identificacao')}")
            resultados.append(norma)
        else:
            print(f"  ❌ FALHA: Norma não encontrada")

    print(f"\n{'=' * 80}")
    print(f"RESULTADO FINAL: {len(resultados)}/{len(casos)} normas extraídas com sucesso.")
    print(f"{'=' * 80}")