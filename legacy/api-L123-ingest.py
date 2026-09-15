"""
ingest_solo.py — Ingestão de normas no grafo-base (Solo) do MCA
Projeto: Motor de Conformidade Aduaneira (MCA) — PIPE FAPESP Fase 1
Documento: RT-001

Este script recebe dados extraídos da API do Senado (via senado_client.py)
e os injeta no Neo4j, criando:
  - Nós: NormativeWork, NormativeComponent, ComponentTemporalVersion, LegislativeAction
  - Arestas: HAS_COMPONENT, HAS_TEMPORAL_VERSION, CREATES

Após a ingestão, valida os invariantes I1, I2 e I3 do E1a.

Uso:
    python ingest_solo.py
"""

import logging
from typing import List, Optional
from neo4j import GraphDatabase
from senado_client import SenadoClient, NormaExtraida

# Configuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Conexão Neo4j (ajustar conforme config.py ou variáveis de ambiente)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "senha_forte_aqui"  # Substituir por variável de ambiente em produção


# =============================================================================
# CLASSE DE INGESTÃO
# =============================================================================

class SoloIngester:
    """Ingestor de normas para o grafo-base (Solo) do MCA."""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self._verify_connection()

    def _verify_connection(self):
        """Verifica a conexão com o Neo4j."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Conexão com Neo4j estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"❌ Falha ao conectar no Neo4j: {e}")
            raise

    def close(self):
        self.driver.close()

    # -------------------------------------------------------------------------
    # Ingestão de Normas
    # -------------------------------------------------------------------------

    def ingest_norma(self, norma: NormaExtraida) -> bool:
        """
        Injeta uma norma extraída da API do Senado no Solo.
        Cria:
          - NormativeWork (a norma abstrata)
          - LegislativeAction (evento causal de criação)
          - ComponentTemporalVersion (versão temporal inicial)
          - Arestas: (Action)-[:CREATES]->(CTV)
        """
        try:
            with self.driver.session() as session:
                # 1. Cria/atualiza o NormativeWork
                session.run("""
                    MERGE (w:NormativeWork {urn: $urn})
                    ON CREATE SET
                        w.tipo = $tipo,
                        w.numero = $numero,
                        w.ano = $ano,
                        w.data_promulgacao = date($data),
                        w.ementa = $ementa,
                        w.situacao = $situacao,
                        w.codigo_senado = $codigo_senado,
                        w.fonte = 'API_Senado_Federal',
                        w.observacao = $observacao
                    ON MATCH SET
                        w.situacao = $situacao,
                        w.ementa = $ementa
                """,
                    urn=norma.urn,
                    tipo=norma.tipo,
                    numero=norma.numero,
                    ano=norma.ano,
                    data=norma.data_promulgacao,
                    ementa=norma.ementa[:2000],  # Limita tamanho
                    situacao=norma.situacao,
                    codigo_senado=norma.codigo_senado,
                    observacao=norma.observacao,
                )

                # 2. Cria o LegislativeAction (evento causal)
                urn_action = f"{norma.urn}!action:criacao"
                session.run("""
                    MERGE (a:LegislativeAction {urn: $urn_action})
                    ON CREATE SET
                        a.action_type = 'CREATES',
                        a.effective_date = date($data),
                        a.source_instrument = $instrumento,
                        a.descricao = $descricao,
                        a.proveniencia_processo_id = $proc_id,
                        a.proveniencia_processo_identificacao = $proc_ident
                """,
                    urn_action=urn_action,
                    data=norma.data_promulgacao,
                    instrumento=f"{norma.tipo} {norma.numero}/{norma.ano}",
                    descricao=f"Criação da {norma.tipo} {norma.numero}/{norma.ano}",
                    proc_id=(norma.processo_origem or {}).get("id"),
                    proc_ident=(norma.processo_origem or {}).get("identificacao"),
                )

                # 3. Cria o CTV inicial (versão temporal da norma completa)
                urn_ctv = f"{norma.urn}@{norma.data_promulgacao}"
                session.run("""
                    MERGE (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                    ON CREATE SET
                        ctv.valid_start = date($data),
                        ctv.valid_end = NULL,
                        ctv.nivel = 0,
                        ctv.componente_tipo = 'Norma_Completa'
                """,
                    urn_ctv=urn_ctv,
                    data=norma.data_promulgacao,
                )

                # 4. Conecta: (Action)-[:CREATES]->(CTV)
                session.run("""
                    MATCH (a:LegislativeAction {urn: $urn_action})
                    MATCH (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                    MERGE (a)-[:CREATES]->(ctv)
                """,
                    urn_action=urn_action,
                    urn_ctv=urn_ctv,
                )

                # 5. Conecta: (Work)-[:HAS_TEMPORAL_VERSION]->(CTV)
                #    (Representa que a Work possui esta versão temporal)
                session.run("""
                    MATCH (w:NormativeWork {urn: $urn_work})
                    MATCH (ctv:ComponentTemporalVersion {urn: $urn_ctv})
                    MERGE (w)-[:HAS_TEMPORAL_VERSION]->(ctv)
                """,
                    urn_work=norma.urn,
                    urn_ctv=urn_ctv,
                )

            logger.info(f"✅ Norma ingerida: {norma.urn}")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao ingerir norma {norma.urn}: {e}")
            return False

    def ingest_lote(self, normas: List[NormaExtraida]) -> dict:
        """Ingesta um lote de normas e retorna estatísticas."""
        sucesso = 0
        falhas = 0
        for norma in normas:
            if self.ingest_norma(norma):
                sucesso += 1
            else:
                falhas += 1
        return {"sucesso": sucesso, "falhas": falhas, "total": len(normas)}

    # -------------------------------------------------------------------------
    # Validação de Invariantes (E1a, Seção 7)
    # -------------------------------------------------------------------------

    def validar_invariante_i1(self) -> int:
        """
        Invariante I1 — Cobertura Temporal Disjunta.
        Verifica que não há sobreposição de intervalos de vigência.
        Retorna: número de violações (esperado: 0).
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:NormativeComponent)-[:HAS_TEMPORAL_VERSION]->(tv1:ComponentTemporalVersion),
                      (c)-[:HAS_TEMPORAL_VERSION]->(tv2:ComponentTemporalVersion)
                WHERE tv1 <> tv2
                  AND tv1.valid_start < tv2.valid_end
                  AND tv2.valid_start < tv1.valid_end
                RETURN count(*) AS violacoes
            """)
            return result.single()["violacoes"]

    def validar_invariante_i2(self) -> int:
        """
        Invariante I2 — Causalidade Fechada.
        Todo CTV (exceto o inicial) deve ter exatamente uma Action que o cria.
        Retorna: número de violações (esperado: 0).
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (ctv:ComponentTemporalVersion)
                WHERE NOT EXISTS { (ctv)<-[:CREATES]-(:LegislativeAction) }
                  AND ctv.valid_start > date('1900-01-01')
                RETURN count(*) AS violacoes
            """)
            return result.single()["violacoes"]

    def validar_invariante_i3(self) -> int:
        """
        Invariante I3 — Agregação sem Redundância.
        CTV pai deve agregar apenas CTVs filhos com valid_start <= seu próprio valid_start.
        Retorna: número de violações (esperado: 0).
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tv_pai:ComponentTemporalVersion)-[:AGGREGATES]->(tv_filho:ComponentTemporalVersion)
                WHERE tv_filho.valid_start > tv_pai.valid_start
                RETURN count(*) AS violacoes
            """)
            return result.single()["violacoes"]

    def validar_todos_invariantes(self) -> dict:
        """Executa todos os invariantes e retorna relatório."""
        i1 = self.validar_invariante_i1()
        i2 = self.validar_invariante_i2()
        i3 = self.validar_invariante_i3()
        return {
            "I1_cobertura_temporal": i1,
            "I2_causalidade_fechada": i2,
            "I3_agregacao": i3,
            "todos_validos": (i1 == 0 and i2 == 0 and i3 == 0),
        }

    # -------------------------------------------------------------------------
    # Estatísticas do Solo
    # -------------------------------------------------------------------------

    def estatisticas(self) -> dict:
        """Retorna estatísticas do grafo-base."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            return {record["label"]: record["count"] for record in result}


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """Fluxo completo: extração → ingestão → validação."""
    logger.info("=" * 80)
    logger.info("INÍCIO DO PIPELINE DE INGESTÃO DO SOLO (MCA)")
    logger.info("=" * 80)

    # 1. Inicializa cliente e ingester
    client = SenadoClient()
    ingester = SoloIngester()

    # 2. Define normas críticas para ingestão inicial (Níveis 1, 2 e 3)
    normas_alvo = [
        # Nível 1 — Constituição (Emendas relevantes para Comex)
        ("EC", 33, 2001, "EC 33/2001 — ICMS Interestadual"),
        ("EC", 45, 2004, "EC 45/2004 — Reforma Tributária"),

        # Nível 2 — Tratados Internacionais
        ("DL", 135, 2019, "DL 135/2019 — Acordo Facilitação Comércio OMC"),

        # Nível 3 — Leis Complementares e Ordinárias
        ("LC", 87, 1996, "LC 87/1996 — Lei Kandir (ICMS Exportação)"),
        ("LEI", 10865, 2004, "Lei 10.865/2004 — PIS/COFINS-Importação"),
        ("LEI", 8032, 1990, "Lei 8.032/1990 — Admissão Temporária"),
        ("LEI", 13670, 2018, "Lei 13.670/2018 — NPI/DUIMP"),
    ]

    # 3. Extrai normas da API
    logger.info(f"\n📥 Extraindo {len(normas_alvo)} normas da API do Senado...")
    normas_extraidas: List[NormaExtraida] = []
    for tipo, numero, ano, desc in normas_alvo:
        logger.info(f"  → {desc}")
        norma = client.buscar_norma_completa(tipo, numero, ano)
        if norma:
            normas_extraidas.append(norma)
        else:
            logger.warning(f"    ⚠️ Não encontrada: {desc}")

    logger.info(f"\n✅ {len(normas_extraidas)}/{len(normas_alvo)} normas extraídas com sucesso.")

    # 4. Ingesta no Neo4j
    logger.info("\n📤 Ingerindo normas no Solo (Neo4j)...")
    stats = ingester.ingest_lote(normas_extraidas)
    logger.info(f"   Sucesso: {stats['sucesso']} | Falhas: {stats['falhas']} | Total: {stats['total']}")

    # 5. Valida invariantes
    logger.info("\n🔍 Validando invariantes de integridade (E1a, Seção 7)...")
    invariantes = ingester.validar_todos_invariantes()
    for nome, valor in invariantes.items():
        status = "✅" if (nome == "todos_validos" and valor) or (nome != "todos_validos" and valor == 0) else "❌"
        logger.info(f"   {status} {nome}: {valor}")

    # 6. Estatísticas finais
    logger.info("\n📊 Estatísticas do Solo:")
    for label, count in ingester.estatisticas().items():
        logger.info(f"   • {label}: {count}")

    # 7. Encerra
    ingester.close()
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE CONCLUÍDO")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()