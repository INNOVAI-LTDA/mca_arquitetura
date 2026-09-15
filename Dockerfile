FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de configuração
COPY pyproject.toml .
COPY src/ src/
COPY rodou/src/ rodou/src/
COPY rodou/requirements.txt rodou/

# Instala dependências do Ro-DOU
RUN pip install --no-cache-dir -r rodou/requirements.txt

# Instala dependências do MCA
RUN pip install --no-cache-dir -e .

# Configura PYTHONPATH para incluir o Ro-DOU
ENV PYTHONPATH="/app:/app/rodou/src:${PYTHONPATH}"

# Usuário não-root
RUN useradd -m -u 1000 mca
USER mca

CMD ["python", "-m", "src.cli"]