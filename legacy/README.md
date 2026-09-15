# ⚠️ Código Legado (NÃO MODIFICAR)

Esta pasta contém os scripts originais do projeto `comex_ont_database`, preservados como **referência** para a refatoração.

## 🚫 Regras

1. **NÃO modificar** nenhum arquivo desta pasta
2. **NÃO importar** código desta pasta no projeto novo
3. **USAR APENAS** como referência para entender a lógica original

## 📦 Arquivos

| Arquivo | Descrição | Destino na Nova Arquitetura |
|---------|-----------|------------------------------|
| `api-L1234-extract.py` | Cliente da API do Senado (L1-L4) | `src/adapters/driving/senado/` |
| `api-L123-ingest.py` | Ingestor Neo4j (SoloIngester) | `src/adapters/driven/neo4j_adapter.py` |
| `parser_tabela_ncm.py` | Parser da Tabela NCM (L5) | `src/adapters/driving/ncm/` |
| `diagnostico_L6.py` | POC do Nível 6 (Querido Diário) | **NÃO refatorar** — será substituído pelo Ro-DOU |

## 📋 Contrato de Refatoração

Ver [`LEGACY_MAP.md`](../LEGACY_MAP.md) para o mapeamento completo de arquivos e o que deve ser preservado 100%.

## 🗑️ Remoção

Esta pasta será removida após a conclusão da refatoração (Sprint 4).
```