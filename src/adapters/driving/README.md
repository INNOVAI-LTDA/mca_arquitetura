# Estrutura inicial
'''
mca-plataforma/
├── src/
│   ├── core/                    # vazia
│   ├── domain/                  # vazia
│   ├── adapters/
│   │   ├── driving/
│   │   │   ├── senado/          # vazia
│   │   │   ├── ncm/             # vazia
│   │   │   └── rodou/           # vazia
│   │   └── driven/              # vazia
│   ├── processors/              # vazia
│   └── utils/                   # vazia
├── tests/
│   ├── domain/                  # vazia
│   ├── adapters/                # vazia
│   └── integration/             # vazia
├── config/
│   └── compositions/            # vazia
├── rodou/                       # submodule (vazio até adicionar)
├── legacy/                      # 🆕 pasta nova
│   ├── api-L1234-extract.py     # ← move daqui
│   ├── api-L123-ingest.py       # ← move daqui
│   ├── parser_tabela_ncm.py     # ← move daqui
│   └── diagnostico_L6.py        # ← move daqui
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
'''