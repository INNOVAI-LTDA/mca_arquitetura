"""
entities.py — Entidades de Domínio do MCA
Arquitetura Hexagonal: Domain Layer

Este módulo define as entidades ricas do domínio, baseadas na ontologia LRMoo
conforme especificado em docs/api/api-L123-doc.md (RT-001).

Entidades principais:
- NormativeWork: Obra normativa abstrata (a "lei" como conceito)
- ComponentTemporalVersion (CTV): Versão temporal de um componente
- LegislativeAction: Evento causal que cria/modifica normas
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormativeWork:
    """
    Representa uma obra normativa abstrata (ex: "Lei 8.032/1990").
    É independente de versões temporais ou componentes físicos.
    
    Atributos conforme RT-001, Seção 4:
    - urn: URN canônico LexML (ex: urn:lex:br:federal:lei:1990-04-09;8032)
    - tipo: Tipo da norma (EMC, DLG, DEC, LEI, LC, etc.)
    - numero: Número da norma
    - ano: Ano da norma
    - data_promulgacao: Data de promulgação (YYYY-MM-DD)
    - ementa: Ementa/descrição da norma
    - situacao: Situação atual (Vigente, Revogada, etc.)
    - codigo_senado: Código interno do Senado (se aplicável)
    - fonte: Fonte dos dados (API_Senado_Federal, DOU, etc.)
    - observacao: Observações adicionais
    - processo_origem: Metadados do processo legislativo
    """
    urn: str
    tipo: str
    numero: str
    ano: int
    data_promulgacao: str
    ementa: str
    situacao: str
    codigo_senado: int | None = None
    fonte: str = "API_Senado_Federal"
    observacao: str | None = None
    processo_origem: dict[str, Any] | None = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converte a entidade para dicionário."""
        return {
            "urn": self.urn,
            "tipo": self.tipo,
            "numero": self.numero,
            "ano": self.ano,
            "data_promulgacao": self.data_promulgacao,
            "ementa": self.ementa,
            "situacao": self.situacao,
            "codigo_senado": self.codigo_senado,
            "fonte": self.fonte,
            "observacao": self.observacao,
            "processo_origem": self.processo_origem,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormativeWork":
        """Cria uma instância a partir de um dicionário."""
        return cls(
            urn=data["urn"],
            tipo=data["tipo"],
            numero=data["numero"],
            ano=data["ano"],
            data_promulgacao=data["data_promulgacao"],
            ementa=data["ementa"],
            situacao=data["situacao"],
            codigo_senado=data.get("codigo_senado"),
            fonte=data.get("fonte", "API_Senado_Federal"),
            observacao=data.get("observacao"),
            processo_origem=data.get("processo_origem", {}),
        )

    def __str__(self) -> str:
        return f"{self.tipo} {self.numero}/{self.ano} ({self.data_promulgacao})"


@dataclass
class ComponentTemporalVersion:
    """
    Representa uma versão temporal de um componente normativo.
    Conforme LRMoo, cada CTV tem um intervalo de vigência bem definido.
    
    Atributos:
    - urn: URN da versão temporal (ex: urn:lex:br:federal:lei:1990-04-09;8032@1990-04-09)
    - valid_start: Início da vigência (YYYY-MM-DD)
    - valid_end: Fim da vigência (YYYY-MM-DD ou None se vigente)
    - nivel: Nível hierárquico (0=norma completa, 1+ = componentes)
    - componente_tipo: Tipo do componente (Norma_Completa, Artigo, Parágrafo, etc.)
    - conteudo: Texto completo do componente (opcional)
    """
    urn: str
    valid_start: str
    valid_end: str | None
    nivel: int
    componente_tipo: str
    conteudo: str | None = None
    work_urn: str | None = None  # Referência ao NormativeWork pai

    def to_dict(self) -> dict[str, Any]:
        """Converte a entidade para dicionário."""
        return {
            "urn": self.urn,
            "valid_start": self.valid_start,
            "valid_end": self.valid_end,
            "nivel": self.nivel,
            "componente_tipo": self.componente_tipo,
            "conteudo": self.conteudo,
            "work_urn": self.work_urn,
        }

    @property
    def vigente(self) -> bool:
        """Verifica se esta versão está vigente."""
        return self.valid_end is None

    def __str__(self) -> str:
        fim = self.valid_end or "vigente"
        return f"CTV[{self.componente_tipo}] {self.valid_start} → {fim}"


@dataclass
class LegislativeAction:
    """
    Representa um evento causal que cria, modifica ou extingue normas.
    Conforme LRMoo, ações legislativas são o mecanismo de transformação.
    
    Atributos:
    - urn: URN da ação (ex: urn:lex:br:federal:lei:1990-04-09;8032!action:criacao)
    - action_type: Tipo de ação (CREATES, AMENDS, REPEALS, MODIFIES)
    - effective_date: Data de efeito da ação (YYYY-MM-DD)
    - source_instrument: Instrumento fonte (ex: "LEI 8032/1990")
    - descricao: Descrição da ação
    - proveniencia_processo_id: ID do processo no Senado
    - proveniencia_processo_identificacao: Identificação do processo
    - target_ctvs: Lista de URNs dos CTVs afetados
    """
    urn: str
    action_type: str
    effective_date: str
    source_instrument: str
    descricao: str
    proveniencia_processo_id: str | None = None
    proveniencia_processo_identificacao: str | None = None
    target_ctvs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Converte a entidade para dicionário."""
        return {
            "urn": self.urn,
            "action_type": self.action_type,
            "effective_date": self.effective_date,
            "source_instrument": self.source_instrument,
            "descricao": self.descricao,
            "proveniencia_processo_id": self.proveniencia_processo_id,
            "proveniencia_processo_identificacao": self.proveniencia_processo_identificacao,
            "target_ctvs": self.target_ctvs,
        }

    def add_target_ctv(self, ctv_urn: str) -> None:
        """Adiciona um CTV alvo da ação."""
        if ctv_urn not in self.target_ctvs:
            self.target_ctvs.append(ctv_urn)

    def __str__(self) -> str:
        return f"{self.action_type}: {self.source_instrument} ({self.effective_date})"


@dataclass
class FetchResult:
    """
    Resultado padronizado de operações de fetch.
    Usado pelos adapters driving para comunicar resultados ao core.
    """
    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
