# Estratégia de Testes

Esta pasta contém a suite de testes do MCA, organizada por camada arquitetural.

## 🎯 Pirâmide de Testes

```
        ┌─────────────┐
        │   E2E (10%) │  ← tests/integration/
        ├─────────────┤
        │ Integração  │  ← tests/adapters/
        │   (20%)     │
        ├─────────────┤
        │  Unitários  │  ← tests/domain/
        │   (70%)     │
        └─────────────┘
```

## 📦 Organização

### `tests/domain/` — Testes do Domínio

Testes unitários das entidades e serviços de domínio:

- `test_entities.py` — Testes das dataclasses (FetchResult, NormativeWork, etc.)
- `test_invariants.py` — **Property-Based Tests** dos invariantes I1, I2, I3 (usando `hypothesis`)

```bash
pytest tests/domain/ -v
```

### `tests/adapters/` — Testes dos Adapters

Testes de integração dos adapters (com mocks de APIs externas):

- `driving/test_senado_adapter.py` — Mock da API do Senado
- `driving/test_ncm_adapter.py` — Parser do JSON NCM
- `driving/test_rodou_adapter.py` — Mock do Ro-DOU
- `driven/test_neo4j_adapter.py` — Mock do driver Neo4j

```bash
pytest tests/adapters/ -v
```

### `tests/integration/` — Testes End-to-End

Testes do pipeline completo (fetch → process → store):

- `test_pipeline_e2e.py` — Valida L1 + L5 → Neo4j → validação I1/I2/I3

```bash
pytest tests/integration/ -v
```

## 🔧 Fixtures Globais

O arquivo `conftest.py` contém fixtures compartilhadas entre todos os testes:

- `mock_senado_api` — Mock da API do Senado
- `mock_neo4j_driver` — Mock do driver Neo4j
- `sample_ncm_json` — JSON de exemplo da Tabela NCM

## 📊 Cobertura de Testes

```bash
# Gerar relatório de cobertura
pytest --cov=src --cov-report=html

# Abrir relatório no navegador
open htmlcov/index.html
```

**Meta**: Cobertura ≥ 80% para componentes críticos (domain, adapters).

## 🚀 Executar Todos os Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Executar apenas testes rápidos (excluir integration)
pytest tests/ -v -m "not integration"

# Executar com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 📖 Convenções

- **Nomes de arquivos**: `test_<componente>.py`
- **Nomes de classes**: `Test<Componente>`
- **Nomes de métodos**: `test_<comportamento_esperado>`
- **Fixtures**: Usar `@pytest.fixture` no `conftest.py`
- **Mocks**: Usar `unittest.mock.patch` ou `pytest-mock`

## 📚 Referências

- [pytest documentation](https://docs.pytest.org/)
- [hypothesis (Property-Based Testing)](https://hypothesis.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
```