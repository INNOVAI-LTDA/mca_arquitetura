# Motor de Conformidade Aduaneira (MCA)

Plataforma unificada de extração hierárquica de 9 níveis normativos, consolidando dados em grafo de conhecimento Neo4j com ontologia LRMoo.

## 🎯 Objetivo

Construir uma base ontológica temporal ("Solo") que represente a hierarquia normativa do comércio exterior brasileiro, permitindo:

- Extração automatizada de normas dos níveis 1-9
- Consolidação em grafo de conhecimento (Neo4j)
- Validação de invariantes de integridade (I1, I2, I3)
- Processamentos posteriores (cross-reference, IA, validação)
- Seleção livre de níveis por cliente/produto

## 🏗️ Arquitetura

**Padrão**: Arquitetura Hexagonal (Ports & Adapters) com Domain-Driven Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Core                               │
│  FetcherPort | IngestPort | URNPort | InvariantsService     │
└─────────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
┌────────┴────────┐                  ┌────────┴────────┐
│ Driving Adapters│                  │ Driven Adapters │
│ (Fontes)        │                  │ (Destinos)      │
│ - Senado (L1-4) │                  │ - Neo4j         │
│ - NCM (L5)      │                  │ - PostgreSQL    │
│ - Ro-DOU (L6)   │                  │                 │
└─────────────────┘                  └─────────────────┘
```

## 📦 Instalação

```bash
# Clonar repositório
git clone https://github.com/innovai-ltda/mca-plataforma.git
cd mca-plataforma

# Adicionar submodule do Ro-DOU
git submodule update --init --recursive

# Instalar dependências
pip install -e .

# Rodar testes
pytest tests/ -v
```

## 🚀 Uso Rápido

```python
from src.core.orchestrator import Orchestrator
from src.adapters.driving.senado.emc_adapter import SenadoEMCAdapter
from src.adapters.driven.neo4j_adapter import Neo4jAdapter

# Configurar fetchers
fetchers = [
    SenadoEMCAdapter(config={"normas": [(33, 2001), (45, 2004)]}),
]

# Configurar storage
ingest = Neo4jAdapter(uri="bolt://localhost:7687", user="neo4j", password="senha")

# Executar pipeline
orchestrator = Orchestrator(fetchers=fetchers, ingest_adapter=ingest)
report = orchestrator.run()
```

## 📚 Documentação

- [Arquitetura](docs/arquitetura.md) — Diagramas e decisões de design
- [Guia de Instalação](docs/guides/instalacao.md) — Como instalar e rodar
- [Como Contribuir](docs/guides/contribuicao.md) — Guidelines de contribuição
- [RT-001](docs/api/api-L123-doc.md) — Relatório técnico original

## ⚖️ Licença

GPL v3 — Ver [LICENSE](LICENSE)

## 📝 Créditos

- **Ro-DOU** — Ministério da Gestão e da Inovação em Serviços Públicos (MGI)
- **API do Senado Federal** — Dados abertos legislativos
- **Tabela NCM** — Planalto/GECEX

---

**Projeto desenvolvido no âmbito do PIPE FAPESP Fase 1 — Atividade AP5 (Graph-RAG Normativo)**
```