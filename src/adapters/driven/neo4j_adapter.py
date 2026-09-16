"""
neo4j_adapter.py — Adapter de Storage para Neo4j
Refatorado para Arquitetura Hexagonal (MCA Project)

Implementa a interface IngestPort para persistência no Neo4j.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date

from src.domain.ports import IngestPort
from src.domain.entities import NormativeWork, LegislativeAction, ComponentTemporalVersion
from src.domain.services import InvariantsService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jAdapter(IngestPort):
    """
    Adapter de storage para Neo4j.
    
    Implementa a interface IngestPort, fornecendo:
    - Persistência idempotente via MERGE
    - Validação de invariantes I1, I2, I3
    - Estatísticas do grafo
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """
        Inicializa conexão com Neo4j.
        
        Args:
            uri: URI do servidor Neo4j
            user: Usuário de autenticação
            password: Senha de autenticação
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Estabelece conexão com Neo4j."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Testa conexão
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"✅ Conexão Neo4j estabelecida: {self.uri}")
        except ImportError:
            logger.warning("⚠️ neo4j driver não instalado. Modo dry-run ativado.")
            self.driver = None
        except Exception as e:
            logger.warning(f"⚠️ Falha ao conectar no Neo4j: {e}. Modo dry-run ativado.")
            self.driver = None
    
    def close(self):
        """Fecha conexão com Neo4j."""
        if self.driver:
            self.driver.close()
    
    def ingerir(self, entity: Any) -> bool:
        """
        Ingere uma única entidade no Neo4j.
        
        Args:
            entity: Entidade (NormativeWork) para ingestão
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.driver:
            logger.info(f"Dry-run: entity pronta para ingestão")
            return True
        
        try:
            if isinstance(entity, NormativeWork):
                self._ingest_work(entity)
                return True
            else:
                logger.error(f"Tipo de entidade não suportado: {type(entity)}")
                return False
        except Exception as e:
            logger.error(f"Erro ao ingerir entity: {e}")
            return False
    
    def ingerir_lote(self, entities: list[Any]) -> dict[str, int]:
        """
        Ingere um lote de entidades no Neo4j.
        
        Args:
            entities: Lista de entidades para ingestão
            
        Returns:
            Estatísticas da ingestão
        """
        if not self.driver:
            logger.info(f"Dry-run: {len(entities)} entities prontas para ingestão")
            return {"sucesso": len(entities), "falha": 0, "total": len(entities)}
        
        sucesso = 0
        falha = 0
        
        for entity in entities:
            if self.ingerir(entity):
                sucesso += 1
            else:
                falha += 1
        
        return {"sucesso": sucesso, "falha": falha, "total": len(entities)}
    
    def validar_invariantes(self) -> dict[str, Any]:
        """
        Valida invariantes I1, I2, I3.
        
        Returns:
            Dicionário com resultados da validação
        """
        if not self.driver:
            return {"todos_validos": True, "dry_run": True}
        
        service = InvariantsService(self.driver)
        return service.validate_all()
    
    def ingest(self, works: List[NormativeWork]) -> int:
        """
        Método legado para compatibilidade.
        Ingere lista de NormativeWorks no Neo4j.
        
        Args:
            works: Lista de NormativeWork para ingestão
            
        Returns:
            Número de trabalhos ingeridos com sucesso
        """
        if not self.driver:
            logger.info(f"Dry-run: {len(works)} works prontos para ingestão")
            return len(works)
        
        ingested_count = 0
        for work in works:
            try:
                self._ingest_work(work)
                ingested_count += 1
            except Exception as e:
                logger.error(f"Erro ao ingerir work {work.urn}: {e}")
        
        return ingested_count
    
    def _ingest_work(self, work: NormativeWork):
        """Ingere um único NormativeWork."""
        with self.driver.session() as session:
            # 1. Cria/atualiza NormativeWork
            session.run("""
                MERGE (w:NormativeWork {urn: $urn})
                ON CREATE SET
                    w.tipo = $tipo,
                    w.numero = $numero,
                    w.ano = $ano,
                    w.data_promulgacao = date($data),
                    w.ementa = $ementa,
                    w.situacao = $situacao,
                    w.fonte = 'MCA_Hexagonal',
                    w.nivel = $nivel
                ON MATCH SET
                    w.situacao = $situacao,
                    w.ementa = $ementa
            """,
                urn=work.urn,
                tipo=work.metadata.get("tipo", ""),
                numero=work.metadata.get("numero", ""),
                ano=work.metadata.get("ano", ""),
                data=str(work.date),
                ementa=work.title[:2000],
                situacao=work.metadata.get("situacao", ""),
                nivel=work.level,
            )
            
            # 2. Cria LegislativeAction
            urn_action = f"{work.urn}!action:criacao"
            session.run("""
                MERGE (a:LegislativeAction {urn: $urn_action})
                ON CREATE SET
                    a.action_type = 'CREATES',
                    a.effective_date = date($data),
                    a.source_instrument = $instrumento,
                    a.descricao = $descricao
            """,
                urn_action=urn_action,
                data=str(work.date),
                instrumento=f"{work.metadata.get('tipo', '')} {work.metadata.get('numero', '')}/{work.metadata.get('ano', '')}",
                descricao=f"Criação da norma {work.urn}",
            )
            
            # 3. Cria ComponentTemporalVersion
            urn_ctv = f"{work.urn}@{work.date}"
            session.run("""
                MERGE (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                ON CREATE SET
                    ctv.valid_start = date($data),
                    ctv.valid_end = NULL,
                    ctv.nivel = 0,
                    ctv.componente_tipo = 'Norma_Completa'
            """,
                urn_ctv=urn_ctv,
                data=str(work.date),
            )
            
            # 4. Conecta Action -> CTV
            session.run("""
                MATCH (a:LegislativeAction {urn: $urn_action})
                MATCH (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                MERGE (a)-[:CREATES]->(ctv)
            """,
                urn_action=urn_action,
                urn_ctv=urn_ctv,
            )
            
            # 5. Conecta Work -> CTV
            session.run("""
                MATCH (w:NormativeWork {urn: $urn_work})
                MATCH (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                MERGE (w)-[:HAS_TEMPORAL_VERSION]->(ctv)
            """,
                urn_work=work.urn,
                urn_ctv=urn_ctv,
            )
        
        logger.debug(f"Work ingerido: {work.urn}")
    
    def validate_invariants(self) -> Dict[str, Any]:
        """
        Valida invariantes I1, I2, I3.
        
        Returns:
            Dicionário com resultados da validação
        """
        if not self.driver:
            return {"todos_validos": True, "dry_run": True}
        
        service = InvariantsService(self.driver)
        return service.validate_all()
    
    def get_statistics(self) -> Dict[str, int]:
        """Retorna estatísticas do grafo."""
        if not self.driver:
            return {}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            return {record["label"]: record["count"] for record in result}
