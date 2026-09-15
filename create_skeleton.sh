#!/bin/bash
# create_skeleton.sh — Cria o esqueleto do repositório MCA

# Pastas com README.md + __init__.py
for dir in \
    "src" \
    "src/core" \
    "src/domain" \
    "src/adapters" \
    "src/adapters/driving" \
    "src/adapters/driving/senado" \
    "src/adapters/driving/ncm" \
    "src/adapters/driving/rodou" \
    "src/adapters/driven" \
    "src/processors" \
    "tests" \
    "config/compositions"; do
    mkdir -p "$dir"
    touch "$dir/__init__.py"
    # README será criado manualmente com conteúdo específico
done

# Pastas com apenas __init__.py (sem README)
for dir in \
    "src/utils" \
    "tests/domain" \
    "tests/adapters" \
    "tests/adapters/driving" \
    "tests/adapters/driven" \
    "tests/integration"; do
    mkdir -p "$dir"
    touch "$dir/__init__.py"
done

# Pastas sem __init__.py nem README (apenas conteúdo)
for dir in \
    "docs/api" \
    "docs/guides" \
    ".github/workflows" \
    "legacy"; do
    mkdir -p "$dir"
done

# READMEs raiz e especiais
touch README.md LEGACY_MAP.md LICENSE NOTICE
touch pyproject.toml Dockerfile docker-compose.yml

echo "✅ Esqueleto criado com sucesso!"