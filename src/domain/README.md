# Camada de Domínio

Esta pasta contém as **entidades de domínio** e **serviços de negócio** do MCA, seguindo os princípios de Domain-Driven Design (DDD).

## 🎯 Responsabilidade

Isolar a lógica de negócio de detalhes de infraestrutura (banco de dados, APIs externas, etc.).

## 📦 Componentes

### `ports.py` — Interfaces (Portas)

Define os contratos que os adapters devem implementar:

- **`FetcherPort`**: Contrato para fontes de dados (Senado, NCM, Ro-DOU)
- **`IngestPort`**: Contrato para destinos de dados (Neo4j, PostgreSQL)
- **`URNPort`**: Contrato para geração e validação de URNs canônicos

### `entities.py` — Entidades de Domínio

Representa os conceitos do modelo LRMoo:

- **`NormativeWork`**: Identidade abstrata da norma (ex: "Lei nº 10.865/2004")
- **`ComponentTemporalVersion` (CTV)**: Versão temporal de um componente
- **`LegislativeAction`**: Evento causal de mudança
- **`FetchResult`**: Contrato unificado de saída para todos os níveis

### `services.py` — Serviços de Domínio

Lógica de negócio pura:

- **`InvariantsService`**: Validação dos invariantes I1, I2, I3
  - **I1 (Cobertura Temporal Disjunta)**: Garante que não há sobreposição de intervalos de vigência
  - **I2 (Causalidade Fechada)**: Todo CTV (exceto inicial) tem exatamente uma LegislativeAction
  - **I3 (Agregação sem Redundância)**: CTV pai agrega apenas CTVs filhos com valid_start ≤ seu próprio valid_start

## 🔗 Dependências

Esta camada **NÃO depende** de:
- ❌ Frameworks externos (FastAPI, Flask, etc.)
- ❌ Bancos de dados (Neo4j, PostgreSQL)
- ❌ APIs externas (Senado, Ro-DOU)

Esta camada **É dependida** por:
- ✅ Camada de adapters (driving e driven)
- ✅ Camada de orquestração (core)

## 🧪 Testes

Os testes desta camada estão em `tests/domain/` e incluem:
- Testes unitários das entidades
- Property-Based Tests dos invariantes (usando `hypothesis`)

```bash
pytest tests/domain/ -v
```

## 📖 Referências

- [IFLA LRMoo](https://www.ifla.org/publications/node/11079/) — Modelo de referência para bibliotecas
- [De Martim, 2025] — SAT-Graph RAG for Legal Norms
- [RT-001](../../docs/api/api-L123-doc.md) — Especificação original do Solo
```