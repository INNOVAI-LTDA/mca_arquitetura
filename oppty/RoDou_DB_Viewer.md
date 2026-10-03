Vou criar um servidor web simples que lê o PostgreSQL e exibe as tabelas em formato tabular.

## Estrutura do Projeto

```
rodou-viewer/
├── server.py
├── templates/
│   └── index.html
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 1. `requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
psycopg2-binary==2.9.9
jinja2==3.1.4
python-multipart==0.0.12
```

## 2. `server.py`

```python
"""
Servidor web para visualizar dados do PostgreSQL do Ro-DOU
"""
import os
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import DictCursor

app = FastAPI(title="Ro-DOU Data Viewer")
templates = Jinja2Templates(directory="templates")

# Configuração do banco de dados
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "user": os.getenv("POSTGRES_USER", "mca"),
    "password": os.getenv("POSTGRES_PASSWORD", "mca_senha"),
    "dbname": os.getenv("POSTGRES_DB", "mca_raw"),
}


def get_db_connection():
    """Cria conexão com o PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)


def get_all_tables(schema: str = "dou_inlabs") -> List[str]:
    """Lista todas as tabelas de um schema"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema,))
            return [row['table_name'] for row in cur.fetchall()]
    finally:
        conn.close()


def get_table_data(table_name: str, schema: str = "dou_inlabs", limit: int = 100) -> Dict[str, Any]:
    """Obtém dados de uma tabela"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Obter estrutura da tabela
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))
            columns = [
                {"name": row['column_name'], "type": row['data_type']}
                for row in cur.fetchall()
            ]
            
            # Obter dados
            cur.execute(f"""
                SELECT * 
                FROM {schema}.{table_name}
                LIMIT %s
            """, (limit,))
            
            rows = []
            for row in cur.fetchall():
                # Converter valores para string para exibição
                row_dict = {}
                for key, value in row.items():
                    if value is None:
                        row_dict[key] = "NULL"
                    elif isinstance(value, (dict, list)):
                        row_dict[key] = str(value)[:200]  # Limitar tamanho
                    else:
                        row_dict[key] = str(value)[:200]
                rows.append(row_dict)
            
            return {
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows),
                "limit": limit
            }
    finally:
        conn.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal com todas as tabelas"""
    schema = "dou_inlabs"
    tables = get_all_tables(schema)
    
    tables_data = []
    for table_name in tables:
        try:
            data = get_table_data(table_name, schema, limit=50)
            tables_data.append({
                "name": table_name,
                "columns": data["columns"],
                "rows": data["rows"],
                "total_rows": data["total_rows"]
            })
        except Exception as e:
            tables_data.append({
                "name": table_name,
                "error": str(e)
            })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tables": tables_data,
            "schema": schema
        }
    )


@app.get("/table/{table_name}", response_class=HTMLResponse)
async def table_detail(request: Request, table_name: str, limit: int = 100):
    """Página de uma tabela específica"""
    schema = "dou_inlabs"
    
    try:
        data = get_table_data(table_name, schema, limit)
        return templates.TemplateResponse(
            "table.html",
            {
                "request": request,
                "table_name": table_name,
                "schema": schema,
                "columns": data["columns"],
                "rows": data["rows"],
                "total_rows": data["total_rows"],
                "limit": limit
            }
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erro ao carregar tabela {table_name}</h1><p>{str(e)}</p>",
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 3. `templates/index.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ro-DOU Data Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
        }
        
        h1 {
            color: #1565c0;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        .schema-info {
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        
        .table-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .table-name {
            color: #1565c0;
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .table-stats {
            color: #666;
            font-size: 0.9em;
        }
        
        .table-link {
            color: #1565c0;
            text-decoration: none;
            font-size: 0.9em;
            padding: 5px 15px;
            border: 1px solid #1565c0;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .table-link:hover {
            background: #1565c0;
            color: white;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
            overflow-x: auto;
            display: block;
        }
        
        .data-table thead {
            background: #1565c0;
            color: white;
        }
        
        .data-table th {
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .data-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #e0e0e0;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .data-table tr:hover {
            background: #f5f5f5;
        }
        
        .data-table tr:nth-child(even) {
            background: #fafafa;
        }
        
        .data-table tr:nth-child(even):hover {
            background: #f0f0f0;
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #c62828;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .column-type {
            font-size: 0.75em;
            color: #999;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Ro-DOU Data Viewer</h1>
        <div class="schema-info">Schema: <strong>{{ schema }}</strong> | Tabelas encontradas: {{ tables|length }}</div>
        
        {% if tables|length == 0 %}
            <div class="no-data">
                <h2>Nenhuma tabela encontrada</h2>
                <p>Verifique se o banco de dados está configurado corretamente.</p>
            </div>
        {% else %}
            {% for table in tables %}
                <div class="table-section">
                    <div class="table-header">
                        <div>
                            <div class="table-name">📊 {{ table.name }}</div>
                            {% if 'error' not in table %}
                                <div class="table-stats">{{ table.total_rows }} registros (mostrando até 50)</div>
                            {% endif %}
                        </div>
                        {% if 'error' not in table %}
                            <a href="/table/{{ table.name }}" class="table-link">Ver completa →</a>
                        {% endif %}
                    </div>
                    
                    {% if 'error' in table %}
                        <div class="error">
                            <strong>Erro ao carregar dados:</strong><br>
                            {{ table.error }}
                        </div>
                    {% elif table.rows|length == 0 %}
                        <div class="no-data">Tabela vazia</div>
                    {% else %}
                        <table class="data-table">
                            <thead>
                                <tr>
                                    {% for col in table.columns %}
                                        <th>
                                            {{ col.name }}
                                            <span class="column-type">{{ col.type }}</span>
                                        </th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for row in table.rows %}
                                    <tr>
                                        {% for col in table.columns %}
                                            <td title="{{ row[col.name] }}">{{ row[col.name] }}</td>
                                        {% endfor %}
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    {% endif %}
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
```

## 4. `templates/table.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ table_name }} - Ro-DOU Data Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #1565c0;
            font-size: 2em;
        }
        
        .back-link {
            color: #1565c0;
            text-decoration: none;
            padding: 10px 20px;
            border: 2px solid #1565c0;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .back-link:hover {
            background: #1565c0;
            color: white;
        }
        
        .table-info {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .table-info h2 {
            color: #1565c0;
            margin-bottom: 10px;
        }
        
        .stats {
            color: #666;
            font-size: 0.9em;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .data-table thead {
            background: #1565c0;
            color: white;
        }
        
        .data-table th {
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .data-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #e0e0e0;
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .data-table tr:hover {
            background: #f5f5f5;
        }
        
        .data-table tr:nth-child(even) {
            background: #fafafa;
        }
        
        .data-table tr:nth-child(even):hover {
            background: #f0f0f0;
        }
        
        .column-type {
            font-size: 0.75em;
            color: #bbdefb;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {{ table_name }}</h1>
            <a href="/" class="back-link">← Voltar</a>
        </div>
        
        <div class="table-info">
            <h2>{{ schema }}.{{ table_name }}</h2>
            <div class="stats">
                Mostrando {{ rows|length }} de {{ total_rows }} registros (limite: {{ limit }})
            </div>
        </div>
        
        {% if rows|length == 0 %}
            <div class="table-info">
                <p>Tabela vazia</p>
            </div>
        {% else %}
            <table class="data-table">
                <thead>
                    <tr>
                        {% for col in columns %}
                            <th>
                                {{ col.name }}
                                <span class="column-type">{{ col.type }}</span>
                            </th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                        <tr>
                            {% for col in columns %}
                                <td title="{{ row[col.name] }}">{{ row[col.name] }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
    </div>
</body>
</html>
```

## 5. `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY server.py .
COPY templates/ templates/

# Expor porta
EXPOSE 8000

# Comando para rodar o servidor
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 6. `docker-compose.yml`

```yaml
version: "3.9"

services:
  rodou-viewer:
    build: .
    container_name: rodou-viewer
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER:-mca}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mca_senha}
      - POSTGRES_DB=${POSTGRES_DB:-mca_raw}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - rodou-network

  postgres:
    image: postgres:17-alpine
    container_name: rodou-postgres
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-mca}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mca_senha}
      - POSTGRES_DB=${POSTGRES_DB:-mca_raw}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-mca}"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - rodou-network

volumes:
  postgres_data:

networks:
  rodou-network:
    driver: bridge
```

## Como Usar

### 1. Subir o servidor

```bash
docker-compose up -d --build
```

### 2. Acessar a página web

Abra o navegador em: **http://localhost:8000**

### 3. Funcionalidades

- **Página principal** (`/`): Mostra todas as tabelas do schema `dou_inlabs` com até 50 registros cada
- **Página da tabela** (`/table/{nome}`): Mostra a tabela completa com até 100 registros

### 4. Conectar ao Ro-DOU existente

Se você já tem o Ro-DOU rodando, modifique o `docker-compose.yml`:

```yaml
services:
  rodou-viewer:
    build: .
    container_name: rodou-viewer
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres  # Nome do container do Ro-DOU
      - POSTGRES_PORT=5432
      - POSTGRES_USER=mca
      - POSTGRES_PASSWORD=mca_senha
      - POSTGRES_DB=mca_raw
    networks:
      - rodou_default  # Rede do Ro-DOU

networks:
  rodou_default:
    external: true
```

Remova o serviço `postgres` do docker-compose.yml e conecte à rede existente do Ro-DOU.

## Estrutura das Tabelas Esperadas

O servidor vai procurar automaticamente por tabelas no schema `dou_inlabs`:

- **`article_raw`**: Publicações brutas do DOU/INLABS
- **`dag_executions`**: Histórico de execuções de DAGs

Cada tabela será exibida em formato tabular com:
- Nome das colunas
- Tipo de dado
- Valores (limitados a 200 caracteres para exibição)
- Link para ver a tabela completa