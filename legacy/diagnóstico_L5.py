"""diagnostico_L5_completo.py — Análise completa dos 6 níveis hierárquicos"""
import json
from collections import Counter, defaultdict
from datetime import datetime

def analisar_arquivo_completo(path: str):
    print(f"Analisando: {path}")
    print("=" * 80)
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Metadados do arquivo
    print(f"\n📋 METADADOS DO ARQUIVO:")
    print(f"   Última atualização: {data.get('Data_Ultima_Atualizacao_NCM', 'N/A')}")
    print(f"   Ato normativo      : {data.get('Ato', 'N/A')}")
    
    # Extrai o array de nomenclaturas
    nomenclaturas = data.get('Nomenclaturas', [])
    print(f"\n📊 Total de itens: {len(nomenclaturas)}")
    
    # Análise por nível (tratando itens que podem ser strings)
    niveis = Counter()
    tipos_ato = Counter()
    formatos_data_fim = Counter()
    exemplos_por_nivel = defaultdict(list)
    itens_invalidos = []
    
    for i, item in enumerate(nomenclaturas):
        # Trata itens que são strings (inválidos)
        if isinstance(item, str):
            itens_invalidos.append((i, item))
            continue
        
        if not isinstance(item, dict):
            itens_invalidos.append((i, f"Tipo inesperado: {type(item).__name__}"))
            continue
        
        codigo = item.get("Codigo", "").replace(".", "")
        nivel = len(codigo)
        niveis[nivel] += 1
        
        # Coleta exemplos (primeiros 3 de cada nível)
        if len(exemplos_por_nivel[nivel]) < 3:
            exemplos_por_nivel[nivel].append({
                "codigo_original": item.get("Codigo"),
                "codigo_limpo": codigo,
                "descricao": item.get("Descricao", "")[:80],
                "data_inicio": item.get("Data_Inicio"),
                "data_fim": item.get("Data_Fim"),
            })
        
        tipos_ato[item.get("Tipo_Ato_Ini", "N/A")] += 1
        formatos_data_fim[item.get("Data_Fim", "N/A")] += 1
    
    # Relatório de itens inválidos
    if itens_invalidos:
        print(f"\n⚠️  ITENS INVÁLIDOS: {len(itens_invalidos)}")
        for idx, item in itens_invalidos[:5]:  # Mostra os primeiros 5
            print(f"   Índice {idx}: {item}")
    
    # Distribuição por nível
    print(f"\n📐 DISTRIBUIÇÃO POR NÍVEL HIERÁRQUICO:")
    nivel_descricao = {
        2: "Capítulo",
        4: "Posição SH",
        5: "Subposição SH 1ª linha (NOVO)",
        6: "Subposição SH 2ª linha",
        7: "Subposição BR intermediária (NOVO)",
        8: "NCM",
    }
    for nivel, count in sorted(niveis.items()):
        desc = nivel_descricao.get(nivel, "?")
        print(f"   Nível {nivel} ({desc:35}): {count:5} itens")
    
    # Tipos de ato
    print(f"\n📜 TIPOS DE ATO NORMATIVO:")
    for tipo, count in tipos_ato.most_common():
        print(f"   {tipo:20}: {count:5}")
    
    # Formatos de Data_Fim
    print(f"\n📅 FORMATOS DE DATA_FIM:")
    for data, count in formatos_data_fim.most_common():
        print(f"   {data:15}: {count:5}")
    
    # Exemplos por nível
    print(f"\n🔍 EXEMPLOS POR NÍVEL:")
    for nivel in sorted(exemplos_por_nivel.keys()):
        print(f"\n   === Nível {nivel} ({nivel_descricao.get(nivel, '?')}) ===")
        for ex in exemplos_por_nivel[nivel]:
            print(f"   Código original : {ex['codigo_original']}")
            print(f"   Código limpo    : {ex['codigo_limpo']}")
            print(f"   Descrição       : {ex['descricao']}...")
            print(f"   Data_Inicio     : {ex['data_inicio']}")
            print(f"   Data_Fim        : {ex['data_fim']}")
            print()

if __name__ == "__main__":
    analisar_arquivo_completo("Tabela_NCM_Vigente_20260905.json")