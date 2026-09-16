"""
classif_client.py — Parser e Cliente para a Tabela NCM Vigente
Projeto: Motor de Conformidade Aduaneira (MCA) — PIPE FAPESP Fase 1
Nível 5 da Hierarquia Normativa: Classificação Fiscal (NCM/TIPI)

Refatorado para Arquitetura Hexagonal.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

NIVEL_TIPO_MAP = {
    2: "CAPITULO",
    4: "POSICAO",
    5: "SUBPOSICAO_SH_1",
    6: "SUBPOSICAO_SH_2",
    7: "SUBPOSICAO_BR",
    8: "NCM",
}

TIPO_ATO_MAP = {
    "Res Gecex": "Resolução GECEX",
    "Res Camex": "Resolução CAMEX",
}

SENTINELA_VIGENCIA = "31/12/9999"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ItemNCM:
    """Representa um item da NCM em qualquer nível hierárquico."""
    codigo_original: str
    codigo_limpo: str
    nivel: int
    tipo: str
    descricao: str
    data_inicio: str
    data_fim: Optional[str]
    tipo_ato: str
    numero_ato: str
    ano_ato: str
    urn: str = ""
    codigo_pai: Optional[str] = None

    def __post_init__(self):
        if not self.urn:
            self.urn = self._gerar_urn()
        if self.codigo_pai is None:
            self.codigo_pai = self._encontrar_pai()

    def _gerar_urn(self) -> str:
        tipo_lower = self.tipo.lower()
        return f"urn:lex:br:merc:{tipo_lower}:{self.codigo_limpo}@{self.data_inicio}"

    def _encontrar_pai(self) -> Optional[str]:
        if self.nivel == 2:
            return None
        elif self.nivel in (5, 7):
            return self.codigo_limpo[:-1]
        else:
            return self.codigo_limpo[:-2]

    @property
    def vigente(self) -> bool:
        return self.data_fim is None or self.data_fim == SENTINELA_VIGENCIA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "codigo_original": self.codigo_original,
            "codigo_limpo": self.codigo_limpo,
            "nivel": self.nivel,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "data_inicio": self.data_inicio,
            "data_fim": self.data_fim,
            "tipo_ato": self.tipo_ato,
            "numero_ato": self.numero_ato,
            "ano_ato": self.ano_ato,
            "urn": self.urn,
            "codigo_pai": self.codigo_pai,
            "vigente": self.vigente,
        }

    def __str__(self) -> str:
        return f"[{self.tipo}] {self.codigo_original} - {self.descricao[:50]}..."


# =============================================================================
# CLIENTE
# =============================================================================

class ClassifClient:
    """
    Cliente para carregar e consultar a Tabela NCM Vigente.
    
    Responsável por:
    - Carregar JSON da NCM
    - Indexar itens por código, nível e descrição
    - Fornecer métodos de busca
    """

    def __init__(self, json_path: Optional[str] = None):
        self.json_path = json_path
        self._items: List[ItemNCM] = []
        self._index_codigo: Dict[str, ItemNCM] = {}
        self._index_nivel: Dict[int, List[ItemNCM]] = defaultdict(list)
        self._metadados: Dict[str, str] = {}
        
        if json_path:
            self.carregar(json_path)

    def carregar(self, json_path: str) -> int:
        """Carrega tabela NCM de arquivo JSON."""
        logger.info(f"Carregando tabela NCM de {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        self._metadados = {
            "data_atualizacao": dados.get("Data_Ultima_Atualizacao_NCM", ""),
            "ato": dados.get("Ato", ""),
        }
        
        nomenclaturas = dados.get("Nomenclaturas", [])
        logger.info(f"Encontradas {len(nomenclaturas)} nomenclaturas")
        
        for item_json in nomenclaturas:
            item = self._parse_item(item_json)
            if item:
                self._items.append(item)
                self._index_codigo[item.codigo_limpo] = item
                self._index_nivel[item.nivel].append(item)
        
        logger.info(f"Carregados {len(self._items)} itens")
        return len(self._items)

    def _parse_item(self, item_json: Dict[str, Any]) -> Optional[ItemNCM]:
        """Parse de um item JSON para ItemNCM."""
        try:
            codigo_original = item_json.get("Codigo", "")
            codigo_limpo = codigo_original.replace(".", "").strip()
            nivel = len(codigo_limpo)
            
            if nivel not in NIVEL_TIPO_MAP:
                return None
            
            tipo = NIVEL_TIPO_MAP[nivel]
            descricao = item_json.get("Descricao", "")
            
            # Parse datas
            data_inicio_raw = item_json.get("Data_Inicio_Vigencia", "")
            data_fim_raw = item_json.get("Data_Fim_Vigencia", "")
            
            data_inicio = self._parse_data(data_inicio_raw)
            data_fim = None if data_fim_raw == SENTINELA_VIGENCIA else self._parse_data(data_fim_raw)
            
            # Parse ato
            tipo_ato_raw = item_json.get("Tipo_Ato", "")
            tipo_ato = TIPO_ATO_MAP.get(tipo_ato_raw, tipo_ato_raw)
            numero_ato = item_json.get("Numero_Ato", "")
            ano_ato = item_json.get("Ano_Ato", "")
            
            return ItemNCM(
                codigo_original=codigo_original,
                codigo_limpo=codigo_limpo,
                nivel=nivel,
                tipo=tipo,
                descricao=descricao,
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipo_ato=tipo_ato,
                numero_ato=numero_ato,
                ano_ato=ano_ato,
            )
        except Exception as e:
            logger.warning(f"Erro ao parse item: {e}")
            return None

    def _parse_data(self, data_str: str) -> str:
        """Converte data DD/MM/YYYY para YYYY-MM-DD."""
        if not data_str or data_str == SENTINELA_VIGENCIA:
            return ""
        try:
            dt = datetime.strptime(data_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return data_str

    def buscar_ncm(self, codigo: str) -> Optional[ItemNCM]:
        """Busca NCM por código."""
        codigo_limpo = codigo.replace(".", "").strip()
        return self._index_codigo.get(codigo_limpo)

    def buscar_por_nivel(self, nivel: int) -> List[ItemNCM]:
        """Retorna todos os itens de um nível."""
        return self._index_nivel.get(nivel, [])

    def buscar_filhos(self, codigo_pai: str) -> List[ItemNCM]:
        """Retorna filhos diretos de um código."""
        codigo_pai_limpo = codigo_pai.replace(".", "").strip()
        return [item for item in self._items if item.codigo_pai == codigo_pai_limpo]

    def buscar_caminho_hierarquico(self, codigo: str) -> List[ItemNCM]:
        """Retorna caminho completo da raiz até o item."""
        codigo_limpo = codigo.replace(".", "").strip()
        item = self._index_codigo.get(codigo_limpo)
        if not item:
            return []

        caminho = [item]
        atual = item
        while atual.codigo_pai:
            pai = self._index_codigo.get(atual.codigo_pai)
            if not pai:
                break
            caminho.append(pai)
            atual = pai

        caminho.reverse()
        return caminho

    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da tabela."""
        vigentes = sum(1 for i in self._items if i.vigente)
        tipos_ato = defaultdict(int)
        for i in self._items:
            tipos_ato[i.tipo_ato] += 1

        return {
            "total": len(self._items),
            "vigentes": vigentes,
            "revogados": len(self._items) - vigentes,
            "por_nivel": {
                NIVEL_TIPO_MAP.get(n, "?"): len(items)
                for n, items in sorted(self._index_nivel.items())
            },
            "tipos_ato": dict(tipos_ato),
            "metadados": self._metadados,
        }
