"""
CLI Entry Point for MCA (Motor de Conformidade Aduaneira)

Usage:
    python -m src.cli --composition mca_completo
    python -m src.cli --composition l6_inteligencia
    python -m src.cli --config custom_config.yaml
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import yaml

from src.core.orchestrator import Orchestrator
from src.adapters.driving.senado.senado_client import SenadoClient
from src.adapters.driving.senado.emc_adapter import EmcAdapter
from src.adapters.driving.senado.dlg_adapter import DlgAdapter
from src.adapters.driving.senado.lei_adapter import LeiOrdinariaComplementarAdapter as LeiAdapter
from src.adapters.driving.senado.dec_adapter import DecAdapter
from src.adapters.driving.ncm.classif_client import ClassifClient
from src.adapters.driving.ncm.ncm_adapter import NcmAdapter
from src.adapters.driven.neo4j_adapter import Neo4jAdapter
from src.adapters.driving.rodou.rodou_factory import RodouFactory
from src.adapters.driving.rodou.dou_adapter import DouAdapter
from src.adapters.driving.rodou.inlabs_adapter import InlabsAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_composition(composition_name: str) -> Dict[str, Any]:
    """Carrega um arquivo de composição YAML pré-definido."""
    config_dir = Path(__file__).parent.parent / "config" / "compositions"
    config_path = config_dir / f"{composition_name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Composição '{composition_name}' não encontrada em {config_dir}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_custom_config(config_path: str) -> Dict[str, Any]:
    """Carrega um arquivo de configuração personalizado."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração '{config_path}' não encontrado.")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_orchestrator(config: Dict[str, Any]) -> Orchestrator:
    """Instancia o Orquestrador baseado na configuração YAML."""
    logger.info("Inicializando componentes...")
    
    # Inicializar Adapters Driven (Storage)
    neo4j_config = config.get("neo4j", {})
    neo4j_adapter = Neo4jAdapter(
        uri=neo4j_config.get("uri", "bolt://localhost:7687"),
        user=neo4j_config.get("user", "neo4j"),
        password=neo4j_config.get("password", "password")
    )
    
    # Inicializar Adapters Driving (Senado)
    senado_client = SenadoClient()
    adapters_senado = []
    
    senado_config = config.get("senado", {})
    if senado_config.get("enabled", True):
        if senado_config.get("levels", {}).get("l1_emc", True):
            adapters_senado.append(EmcAdapter(senado_client))
        if senado_config.get("levels", {}).get("l2_dlg", True):
            adapters_senado.append(DlgAdapter(senado_client))
        if senado_config.get("levels", {}).get("l3_lei", True):
            adapters_senado.append(LeiAdapter(senado_client))
        if senado_config.get("levels", {}).get("l4_dec", True):
            adapters_senado.append(DecAdapter(senado_client))
    
    # Inicializar Adapters Driving (NCM)
    ncm_adapters = []
    ncm_config = config.get("ncm", {})
    if ncm_config.get("enabled", True):
        classif_client = ClassifClient()
        ncm_adapters.append(NcmAdapter(classif_client))
    
    # Inicializar Adapters Driving (Ro-DOU / Nível 6)
    rodou_adapters = []
    rodou_config = config.get("rodou", {})
    if rodou_config.get("enabled", False):
        rodou_factory = RodouFactory()
        # O factory gerencia a instância única do Ro-DOU
        if rodou_config.get("sources", {}).get("dou", True):
            rodou_adapters.append(DouAdapter(rodou_factory))
        if rodou_config.get("sources", {}).get("inlabs", False):
            rodou_adapters.append(InlabsAdapter(rodou_factory))
    
    # Montar o orchestrator
    orchestrator = Orchestrator(
        storage=neo4j_adapter,
        senado_adapters=adapters_senado,
        ncm_adapters=ncm_adapters,
        rodou_adapters=rodou_adapters
    )
    
    return orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Motor de Conformidade Aduaneira (MCA) - CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--composition",
        type=str,
        help="Nome da composição pré-definida (ex: mca_completo, l6_inteligencia)"
    )
    group.add_argument(
        "--config",
        type=str,
        help="Caminho para um arquivo de configuração YAML personalizado"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa sem persistir dados no Neo4j (apenas validação)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.composition:
            logger.info(f"Carregando composição: {args.composition}")
            config = load_composition(args.composition)
        else:
            logger.info(f"Carregando configuração personalizada: {args.config}")
            config = load_custom_config(args.config)
        
        orchestrator = build_orchestrator(config)
        
        logger.info("Iniciando pipeline de ingestão...")
        results = orchestrator.run(dry_run=args.dry_run)
        
        logger.info("Pipeline concluído com sucesso.")
        logger.info(f"Resumo: {results}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Erro de configuração: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Erro crítico durante a execução: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
