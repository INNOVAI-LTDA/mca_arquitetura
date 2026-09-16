"""
__init__.py — Pacote de adapters do Senado
"""

from src.adapters.driving.senado.senado_client import SenadoClient, NormaExtraida
from src.adapters.driving.senado.emc_adapter import EmendaConstitucionalAdapter
from src.adapters.driving.senado.dlg_adapter import DecretoLegislativoAdapter
from src.adapters.driving.senado.lei_adapter import LeiAdapter
from src.adapters.driving.senado.dec_adapter import DecretoAdapter

__all__ = [
    "SenadoClient",
    "NormaExtraida",
    "EmendaConstitucionalAdapter",
    "DecretoLegislativoAdapter",
    "LeiAdapter",
    "DecretoAdapter",
]