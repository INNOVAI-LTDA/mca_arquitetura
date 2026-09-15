#!/bin/bash
# cleanup_duplications.sh

echo "🧹 Limpando duplicações..."

# Remove a cópia duplicada dentro de config/
rm -rf config/src
rm -rf config/tests
rm -rf config/config

# Move arquivos que deveriam estar na raiz
mv config/docker-compose.yml . 2>/dev/null || true
mv config/Dockerfile . 2>/dev/null || true
mv config/LEGACY_MAP.md . 2>/dev/null || true
mv config/LICENSE . 2>/dev/null || true  # sobrescreve se vazio
mv config/NOTICE . 2>/dev/null || true
mv config/pyproject.toml . 2>/dev/null || true

# Mantém apenas compositions/ dentro de config/
# (remove README duplicado de config/ se não for específico)
rm -f config/README.md

echo "✅ Duplicações removidas"