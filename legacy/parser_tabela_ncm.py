"""
classif_client.py — Parser e Cliente para a Tabela NCM Vigente
Projeto: Motor de Conformidade Aduaneira (MCA) — PIPE FAPESP Fase 1
Nível 5 da Hierarquia Normativa: Classificação Fiscal (NCM/TIPI)

Estrutura real do JSON (confirmada por diagnóstico em 2026-09-05):
  - Raiz: dict com chaves [Data_Ultima_Atualizacao_NCM, Ato, Nomenclaturas]
  - Nomenclaturas: array com 15.156 itens
  - 6 níveis hierárquicos: 2 (Capítulo), 4 (Posição), 5 (Subposição SH 1ª),
    6 (Subposição SH 2ª), 7 (Subposição BR), 8 (NCM)
  - Tipos de ato: "Res Gecex" (15.134), "Res Camex" (22)
  - Sentinela de vigência: "31/12/9999"
  - Datas no formato DD/MM/YYYY

Uso:
    from classif_client import ClassifClient

    client = ClassifClient("Tabela_NCM_Vigente_20260905.json")
    ncm = client.buscar_ncm("84713012")
    print(ncm)
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

# Mapeamento de nível → tipo de componente (conforme E1a)
NIVEL_TIPO_MAP = {
    2: "CAPITULO",
    4: "POSICAO",
    5: "SUBPOSICAO_SH_1",
    6: "SUBPOSICAO_SH_2",
    7: "SUBPOSICAO_BR",
    8: "NCM",
}

# Mapeamento de tipo de ato → nome normalizado
TIPO_ATO_MAP = {
    "Res Gecex": "Resolução GECEX",
    "Res Camex": "Resolução CAMEX",
}

# Sentinela de vigência usada pelo sistema
SENTINELA_VIGENCIA = "31/12/9999"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ItemNCM:
    """Representa um item da NCM em qualquer nível hierárquico."""
    codigo_original: str   # Com pontos: "8471.30.12"
    codigo_limpo: str      # Sem pontos: "84713012"
    nivel: int             # 2, 4, 5, 6, 7 ou 8
    tipo: str              # CAPITULO, POSICAO, etc.
    descricao: str
    data_inicio: str       # YYYY-MM-DD
    data_fim: Optional[str]  # YYYY-MM-DD ou None (vigente)
    tipo_ato: str          # "Resolução GECEX"
    numero_ato: str
    ano_ato: str
    urn: str = ""
    codigo_pai: Optional[str] = None  # Código limpo do pai hierárquico

    def __post_init__(self):
        if not self.urn:
            self.urn = self._gerar_urn()
        if self.codigo_pai is None:
            self.codigo_pai = self._encontrar_pai()

    def _gerar_urn(self) -> str:
        tipo_lower = self.tipo.lower()
        return f"urn:lex:br:merc:{tipo_lower}:{self.codigo_limpo}@{self.data_inicio}"

    def _encontrar_pai(self) -> Optional[str]:
        """Encontra o código do pai hierárquico."""
        if self.nivel == 2:
            return None
        elif self.nivel in (5, 7):
            return self.codigo_limpo[:-1]
        else:  # 4, 6, 8
            return self.codigo_limpo[:-2]

    @property
    def vigente(self) -> bool:
        return self.data_fim is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "codigo": self.codigo_limpo,
            "codigo_original": self.codigo_original,
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
        }

    def __str__(self) -> str:
        fim = self.data_fim or "vigente"
        return f"[{self.tipo:20}] {self.codigo_original:12} {self.descricao[:50]} ({self.data_inicio} → {fim})"


# =============================================================================
# CLIENTE
# =============================================================================

class ClassifClient:
    """Parser e cliente para a Tabela NCM Vigente."""

    def __init__(self, path_json: str):
        self.path_json = path_json
        self._items: List[ItemNCM] = []
        self._index_codigo: Dict[str, ItemNCM] = {}
        self._index_nivel: Dict[int, List[ItemNCM]] = defaultdict(list)
        self._metadados: Dict[str, str] = {}
        self._carregar()

    def _carregar(self):
        """Carrega e parseia o arquivo JSON."""
        logger.info(f"Carregando: {self.path_json}")

        with open(self.path_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._metadados = {
            "atualizacao": data.get("Data_Ultima_Atualizacao_NCM", ""),
            "ato": data.get("Ato", ""),
        }

        nomenclaturas = data.get("Nomenclaturas", [])
        logger.info(f"Total de itens brutos: {len(nomenclaturas)}")

        for item_raw in nomenclaturas:
            if not isinstance(item_raw, dict):
                continue

            item = self._parse_item(item_raw)
            if item:
                self._items.append(item)
                self._index_codigo[item.codigo_limpo] = item
                self._index_nivel[item.nivel].append(item)

        logger.info(f"✅ {len(self._items)} itens parseados com sucesso")
        for nivel in sorted(self._index_nivel.keys()):
            tipo = NIVEL_TIPO_MAP.get(nivel, "?")
            logger.info(f"   Nível {nivel} ({tipo}): {len(self._index_nivel[nivel])}")

    def _parse_item(self, raw: Dict) -> Optional[ItemNCM]:
        """Converte um item bruto do JSON em ItemNCM."""
        codigo_original = raw.get("Codigo", "").strip()
        if not codigo_original:
            return None

        codigo_limpo = codigo_original.replace(".", "")
        nivel = len(codigo_limpo)

        if nivel not in NIVEL_TIPO_MAP:
            return None

        # Converte data_inicio
        data_inicio_raw = raw.get("Data_Inicio", "")
        data_inicio = self._converter_data(data_inicio_raw)
        if not data_inicio:
            return None

        # Converte data_fim (sentinela → None)
        data_fim_raw = raw.get("Data_Fim", "")
        data_fim = self._converter_data(data_fim_raw)

        # Normaliza tipo de ato
        tipo_ato_raw = raw.get("Tipo_Ato_Ini", "")
        tipo_ato = TIPO_ATO_MAP.get(tipo_ato_raw, tipo_ato_raw)

        return ItemNCM(
            codigo_original=codigo_original,
            codigo_limpo=codigo_limpo,
            nivel=nivel,
            tipo=NIVEL_TIPO_MAP[nivel],
            descricao=raw.get("Descricao", ""),
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipo_ato=tipo_ato,
            numero_ato=raw.get("Numero_Ato_Ini", ""),
            ano_ato=raw.get("Ano_Ato_Ini", ""),
        )

    @staticmethod
    def _converter_data(data_str: str) -> Optional[str]:
        """Converte DD/MM/YYYY → YYYY-MM-DD. Sentinela → None."""
        if not data_str or data_str == SENTINELA_VIGENCIA:
            return None
        try:
            return datetime.strptime(data_str[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None

    # -------------------------------------------------------------------------
    # Consultas
    # -------------------------------------------------------------------------

    def buscar_ncm(self, codigo: str) -> Optional[ItemNCM]:
        """Busca item por código (com ou sem pontos)."""
        codigo_limpo = codigo.replace(".", "").strip()
        return self._index_codigo.get(codigo_limpo)

    def buscar_por_nivel(self, nivel: int) -> List[ItemNCM]:
        """Retorna todos os itens de um nível hierárquico."""
        return self._index_nivel.get(nivel, [])

    def buscar_filhos(self, codigo_pai: str) -> List[ItemNCM]:
        """Retorna os filhos diretos de um item."""
        codigo_pai_limpo = codigo_pai.replace(".", "").strip()
        return [
            item for item in self._items
            if item.codigo_pai == codigo_pai_limpo
        ]

    def buscar_caminho_hierarquico(self, codigo: str) -> List[ItemNCM]:
        """
        Retorna o caminho completo da raiz até o item.
        Ex: Capítulo → Posição → Subposição SH1 → Subposição SH2 → Subposição BR → NCM
        """
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

    def buscar_ncms_vigentes(self, data: str) -> List[ItemNCM]:
        """Retorna todos os itens vigentes em uma data (YYYY-MM-DD)."""
        return [
            item for item in self._items
            if item.data_inicio <= data
            and (item.data_fim is None or item.data_fim > data)
        ]

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

    @property
    def metadados(self) -> Dict[str, str]:
        return self._metadados


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE: ClassifClient — Parser da Tabela NCM Vigente")
    print("=" * 80)

    client = ClassifClient("Tabela_NCM_Vigente_20260905.json")

    # Estatísticas
    print("\n📊 ESTATÍSTICAS:")
    stats = client.estatisticas()
    print(f"   Total: {stats['total']} | Vigentes: {stats['vigentes']} | Revogados: {stats['revogados']}")
    print(f"   Ato: {stats['metadados']['ato']}")

    # Busca específica
    print("\n🔍 BUSCA ESPECÍFICA (8471.30.12):")
    ncm = client.buscar_ncm("8471.30.12")
    if ncm:
        print(f"   {ncm}")
        print(f"   URN: {ncm.urn}")
        print(f"   Pai: {ncm.codigo_pai}")

    # Caminho hierárquico
    print("\n🌳 CAMINHO HIERÁRQUICO (8471.30.12):")
    caminho = client.buscar_caminho_hierarquico("8471.30.12")
    for item in caminho:
        indent = "   " * (item.nivel // 2)
        print(f"{indent}└── {item}")

    # Filhos de uma posição
    print("\n📂 FILHOS DA POSIÇÃO 8471:")
    filhos = client.buscar_filhos("8471")
    for f in filhos[:5]:
        print(f"   • {f}")
    if len(filhos) > 5:
        print(f"   ... e mais {len(filhos) - 5}")

    print("\n" + "=" * 80)