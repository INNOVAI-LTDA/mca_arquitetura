# Adapter do Senado Federal (Níveis 1-4)

Esta pasta contém os adapters que implementam `FetcherPort` para os Níveis 1-4 da hierarquia normativa, consumindo a API de Dados Abertos do Senado Federal.

## 🎯 Responsabilidade

Extrair metadados de normas federais (Emendas, Decretos Legislativos, Leis, Decretos) da API do Senado e convertê-los para o contrato `FetchResult`.

## 📦 Componentes

### `senado_client.py` — Cliente HTTP (Reaproveitado 100%)

Cliente original do projeto `comex_ont_database`, preservado sem alterações:

- **Rate limiting**: 10 req/s (margem de segurança)
- **Retry com backoff exponencial**: 3 tentativas
- **Conversão automática de siglas**: `EC→EMC`, `DL→DLG`
- **Geração de URN canônico**: Padrão `urn:lex:br:federal:...`
- **Parsing robusto do JSON**: Trata estrutura `DetalheDocumento → documentos → documento`

### Adapters por Nível

Cada adapter implementa `FetcherPort` e delega ao `SenadoClient`:

| Adapter | Nível | Tipo de Norma | Sigla API |
|---------|-------|---------------|-----------|
| `emc_adapter.py` | 1 | Emenda Constitucional | `EMC` |
| `dlg_adapter.py` | 2 | Decreto Legislativo | `DLG` |
| `lei_adapter.py` | 3 | Lei (LC e LEI) | `LC`, `LEI` |
| `dec_adapter.py` | 4 | Decreto | `DEC` |

## 🔗 Dependências

- **Depende de**: `src/domain/ports.py` (FetcherPort, FetchResult)
- **Depende de**: `senado_client.py` (lógica HTTP preservada)
- **É usado por**: `src/core/orchestrator.py`

## 🧪 Testes

```bash
pytest tests/adapters/driving/test_senado_adapter.py -v
```

Os testes mockam a API do Senado (não fazem requisições reais).

## 📖 Exemplo de Uso

```python
from src.adapters.driving.senado.emc_adapter import SenadoEMCAdapter

adapter = SenadoEMCAdapter(config={
    "normas": [(33, 2001), (45, 2004)]
})

result = adapter.fetch(reference_date=datetime(2026, 9, 15))
print(f"Extraídas {result.items_count} normas")
print(f"URNs: {result.urns}")
```

## 📚 Documentação da API

- [API do Senado Federal](https://legis.senado.leg.br/dadosabertos/)
- [RT-001 — Seção 3](../../../../docs/api/api-L123-doc.md#3-mapeamento-de-fontes-de-dados-api-do-senado-federal)
```