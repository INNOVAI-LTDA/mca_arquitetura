"""
fetch_L6_querido_diario.py — Extração de INs RFB via API do Querido Diário (Engine do Ro-DOU)
Nível 6 da Hierarquia Normativa: Regulamentação Aduaneira
Projeto: Motor de Conformidade Aduaneira (MCA) — PIPE FAPESP Fase 1

Baseado na documentação oficial do Ro-DOU: 
https://gestaogovbr.github.io/Ro-dou/como_funciona/pesquisa_dou/
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Endpoint da API Pública do Querido Diário (usado pelo Ro-DOU)
QD_API_URL = "https://api.queridodiario.ok.org.br/gazettes"

# Headers básicos (a API é pública, mas é boa prática identificar o client)
HEADERS = {
    "User-Agent": "MCA-Project/1.0 (PIPE-FAPESP; diego@daleship.com.br)",
    "Accept": "application/json",
}

def buscar_dou(
    termo_busca: str, 
    data_inicio: str = None, 
    data_fim: str = None,
    tamanho_excerto: int = 500,
    limite_resultados: int = 10
) -> List[Dict]:
    """
    Busca publicações no DOU usando a API do Querido Diário.
    
    Args:
        termo_busca: Query string (suporta operadores booleanos, ex: "RFB" AND "NCM")
        data_inicio: Data no formato YYYY-MM-DD (opcional)
        data_fim: Data no formato YYYY-MM-DD (opcional)
        tamanho_excerto: Tamanho do snippet de texto retornado
        limite_resultados: Número máximo de resultados por página
        
    Returns:
        Lista de dicionários com os metadados das publicações encontradas.
    """
    params = {
        "querystring": termo_busca,
        "excerpt_size": tamanho_excerto,
        "size": limite_resultados,
        "sort_by": "descending_date"  # Ordena do mais recente para o mais antigo
    }
    
    if data_inicio:
        params["published_since"] = data_inicio
    if data_fim:
        params["published_until"] = data_fim

    logger.info(f"Buscando no Querido Diário: '{termo_busca}'")
    logger.info(f"Endpoint: {QD_API_URL}")
    
    try:
        response = requests.get(QD_API_URL, params=params, headers=HEADERS, timeout=15,verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        # A API retorna um objeto com a chave "gazettes" contendo a lista
        publicacoes = data.get("gazettes", [])
        
        if not publicacoes:
            logger.warning("Nenhuma publicação encontrada para os critérios especificados.")
            return []
            
        logger.info(f"✅ {len(publicacoes)} publicação(ões) encontrada(s).")
        
        resultados_formatados = []
        for pub in publicacoes:
            resultados_formatados.append({
                "data": pub.get("date"),
                "territory_name": pub.get("territory_name", "Desconhecido"), # Ex: "União" para DOU
                "url": pub.get("url"),
                "txt_url": pub.get("txt_url"), # Link direto para o texto puro (ouro para o parser!)
                "excerpts": pub.get("excerpts", []) # Trechos do texto onde o termo foi encontrado
            })
            
        return resultados_formatados
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Erro de conexão (DNS/Proxy): {e}")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Erro HTTP: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return []

# =============================================================================
# FLUXO PRINCIPAL DE TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("FETCH NÍVEL 6: INs RFB via API Querido Diário (Engine do Ro-DOU)")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Definir janela de tempo (ex: últimos 6 meses para capturar as INs críticas)
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=180)
    
    # Query otimizada para encontrar Instruções Normativas da RFB
    QUERY_TESTE = '"Instrução Normativa" AND "RFB" AND ("NCM" OR "aduaneiro" OR "comércio exterior")'
    
    print(f"\n🔍 Query: {QUERY_TESTE}")
    print(f"📅 Período: {data_inicio.strftime('%Y-%m-%d')} a {data_fim.strftime('%Y-%m-%d')}\n")
    
    resultados = buscar_dou(
        termo_busca=QUERY_TESTE,
        data_inicio=data_inicio.strftime("%Y-%m-%d"),
        data_fim=data_fim.strftime("%Y-%m-%d"),
        limite_resultados=15
    )
    
    if resultados:
        print(f"\n📊 RESULTADOS ENCONTRADOS ({len(resultados)}):")
        print("-" * 80)
        for i, res in enumerate(resultados, 1):
            print(f"[{i:02d}] Data: {res['data']} | Fonte: {res['territory_name']}")
            
            # Mostra o primeiro excerto (ementa/snippet) se existir
            if res['excerpts']:
                excerto = res['excerpts'][0].get('text', '')
                # Limpa quebras de linha excessivas para exibição
                excerto_limpo = ' '.join(excerto.split())
                print(f"     📝 Trecho: {excerto_limpo[:150]}...")
            
            print(f"     🔗 Texto Puro: {res['txt_url']}")
            print()
            
        print("=" * 80)
        print("✅ FETCH BEM-SUCEDIDO! O domínio do Querido Diário foi acessível.")
        print("💡 PRÓXIMO PASSO: Usar o campo 'txt_url' para baixar o texto completo")
        print("   e alimentá-lo no parser de hierarquia (extrator_L6_local.py).")
    else:
        print("\n❌ Nenhuma publicação encontrada ou falha na conexão.")
        print("   Verifique se o termo de busca está muito restritivo.")