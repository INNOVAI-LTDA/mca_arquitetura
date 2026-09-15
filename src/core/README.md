# Camada de Orquestração (Core)

Esta pasta contém os componentes centrais que orquestram o pipeline de extração → processamento → ingestão.

## 🎯 Responsabilidade
Coordenar a execução dos fetchers, aplicar processors e delegar ao storage, sem conhecer detalhes de implementação.

## 📦 Componentes

### `orchestrator.py`
Executa fetchers em paralelo, consolida resultados e delega ao pipeline.

### `pipeline.py`
Define o fluxo `fetch → process → store` com injeção de dependências.

### `exceptions.py`
Exceções específicas do domínio (ex: `InvariantViolationError`, `FetcherConfigError`).

## 🔗 Dependências
- **Depende de**: `src/domain/` (portas e entidades)
- **É usado por**: `src/cli.py` (entrypoint)

## 🧪 Testes
```bash
pytest tests/integration/ -v