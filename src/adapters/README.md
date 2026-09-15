# Camada de Adapters

Implementa o padrão **Ports & Adapters** (Arquitetura Hexagonal).

## 🎯 Responsabilidade
Traduzir entre o domínio (portas) e o mundo externo (APIs, bancos, bibliotecas).

## 📦 Sub-pastas

### `driving/` — Fontes de Dados (Entrada)
Adapters que **alimentam** o sistema com dados externos:
- `senado/` — API do Senado Federal (Níveis 1-4)
- `ncm/` — Tabela NCM/Planalto (Nível 5)
- `rodou/` — Ro-DOU como biblioteca (Nível 6)

### `driven/` — Destinos (Saída)
Adapters que **consomem** os dados processados:
- `neo4j_adapter.py` — Grafo de conhecimento (Solo)
- `postgres_adapter.py` — Dados brutos normalizados

## 🔗 Princípio da Dependência
> **Adapters dependem do domínio, nunca o contrário.**

O domínio (`src/domain/`) define as portas (`FetcherPort`, `IngestPort`).
Os adapters implementam essas portas.