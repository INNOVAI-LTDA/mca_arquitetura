# LEGACY_MAP.md — Contrato de Refatoração

## Arquivos de Origem (fonte da verdade)

| Arquivo Legacy | Destino na Nova Arquitetura | O que PRESERVAR 100% |
|----------------|------------------------------|----------------------|
| `legacy/api-L1234-extract.py` | `src/adapters/driving/senado/senado_client.py` + adapters `emc_adapter.py`, `dlg_adapter.py`, `lei_adapter.py`, `dec_adapter.py` | - Lógica de `_converter_sigla()`<br/>- Rate limit (10 req/s)<br/>- Retry com backoff exponencial<br/>- Geração de URN canônico<br/>- Parsing do `DetalheDocumento` |
| `legacy/parser_tabela_ncm.py` | `src/adapters/driving/ncm/classif_client.py` + `ncm_adapter.py` | - Parsing do JSON NCM (6 níveis)<br/>- Sentinela `31/12/9999` → `None`<br/>- Busca hierárquica (pai→filho)<br/>- Conversão DD/MM/YYYY → YYYY-MM-DD |
| `legacy/api-L123-ingest.py` | `src/adapters/driven/neo4j_adapter.py` | - Queries MERGE idempotentes<br/>- Criação de NormativeWork, CTV, LegislativeAction<br/>- Validação de invariantes I1, I2, I3 |
| `legacy/diagnostico_L6.py` | **NÃO refatorar** — será substituído pelo Ro-DOU (submodule) | — |

## Regras Invioláveis

1. **Nenhum arquivo legacy deve ser modificado** — apenas lido como referência
2. **Cada adapter novo deve ter testes unitários** cobrindo ≥ 80%
3. **URNs gerados devem ser idênticos** aos gerados pelo código legacy
4. **Invariantes I1, I2, I3 devem passar** após cada ingestão
5. **Ro-DOU deve ser adicionado como submodule** (tag 0.13.0)