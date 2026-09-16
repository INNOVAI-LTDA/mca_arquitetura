"""
Factory para inicialização do Ro-DOU

Gerencia o ciclo de vida da instância única do Ro-DOU.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RodouFactory:
    """
    Factory singleton para gerenciar a instância do Ro-DOU.
    
    O Ro-DOU é uma biblioteca externa que deve ser inicializada
    apenas uma vez por processo. Esta factory garante isso.
    """
    
    _instance: Optional[Any] = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> Any:
        """
        Retorna a instância única do Ro-DOU.
        
        Returns:
            Instância do objeto Searcher do Ro-DOU
        """
        if not cls._initialized:
            try:
                # Importa o módulo do submodule rodou
                from rodou.searcher import Searcher
                
                cls._instance = Searcher()
                cls._initialized = True
                logger.info("Ro-DOU instance initialized successfully")
                
            except ImportError as e:
                logger.error(f"Failed to import Ro-DOU: {e}")
                logger.warning("Ro-DOU functionality will be unavailable")
                cls._instance = None
                cls._initialized = True
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reseta o estado da factory (útil para testes)."""
        cls._instance = None
        cls._initialized = False
