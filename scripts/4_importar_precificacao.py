"""
4_importar_precificacao.py
Importa TAXA_E_LUCRO, Produto (shipping), Saldos (estoque),
tabelas de custo Qualy Air, e calcula o preço ideal por marketplace.
"""

import pandas as pd
import math
import os
from pathlib import Path
from schema import get_connection, criar_tabelas

INPUT = Path(__file__).parent.parent / "data" / "input"

PRICE_FILES = [
    'Qualy_Air_RN__NV.xlsx', 'Qualy_Air_LY__CA.xlsx', 'Qualy_Air_SB__PA.xlsx',
    'Qualy_Air_RN__FL.xlsx', 'Qualy_Air_RN__TX.xlsx', 'Qualy_Air_PBI__CA.xlsx',
    'Qualy_Air_PBI__TX.xlsx', 'Qualy_Air_PBI__VA.xlsx', 'Qualy_Air_GPD__GA.xlsx',
    'Qualy_Air_KCA__CA.xlsx', 'Qualy_Air_LY__VA.xlsx', 'Qualy_Air_MT__NJ.xlsx',
    'Qualy_Air_UAC__TX.xlsx', 'Qualy_Air_DNA__CA.xlsx', 'Qualy_Air_RN__OS.xlsx',
    'TAXA_E_LUCRO.xlsx', 'Planilha_precificacao.xlsx', 'Planilha_precificacao_LEVE.xlsx',
]

PRIORITY_MAP = {
    'Qualy Air (RN) - NV': 1, 'Qualy Air (RN) - TX': 2,
    'Qualy Air (RN) - FL': 3, 'Qualy Air (RN) - OS': 4,
    'Qualy Air (LY) - VA': 1, 'Qualy Air (LY) - CA': 2,
    'Qualy Air (PBI) - TX': 1, 'Qualy Air (PBI) - VA': 2, 'Qualy Air (PBI) - CA': 3,
}

MKP_COLS = {
    'Stock AC':               'preco_stock_ac',
    'QUALY AIR':              'preco_qualy_air',
    'Qualy Air Shopify':      'preco_shopify',
    'Walmart US':             'preco_walmart',
    'Qualy Air - Amazon US':  'preco_amazon',
    'Ebay-Forceparts':        'preco_forceparts',
}


def safe_float(v):
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except:
        return None


def round_price(raw, arred):
    cents = int(arred) / 100.0
    base = math.floor(raw)
    candidate = base + cents
    if candidate < raw:
        candidate += 1
    return candidate


def importar():
    # Verificar arquivos obrigatórios
    for req in ['TAXA_E_LUCRO.xlsx', 'Produto.xlsx', 'Saldos_de_Estoque.xlsx']:
        if not (INPUT / req).exists():
            print(f"❌ Arquivo obrigatório não encontrado: {req}")
            return

    # --- TAXA E LUCRO ---
    print("  📥 Lendo taxas e lucros...")
    taxa_df = pd.read_excel(INPUT / "TAXA_E_LUCRO.xlsx")
    taxa_df.columns = taxa_df.columns.str.strip()
    taxa_df['Taxa_num'] = taxa_df['Taxa'].astype(str).str.replace('%', '').str.strip().astype(float) / 100
    taxa_df['Lucro_num'] = taxa_df['Lucro'].astype(str).str.replace('%', '').str.strip().astype(float) / 100
    taxa_dict = {}
    for _, r in taxa_df.iterrows():
        taxa_dict[(r['Categoria'], r['Name'])] = (r['Taxa_num'], r['Lucro_num'], int(r['Arredondamento']))

    conn = get_connection()
    cur = conn.cursor()

    # Salva taxa_lucro no banco
    cur.execute("DELETE FROM taxa_lucro")
    for _, r in taxa_df.iterrows():
        cur.execute("""
            INSERT OR REPLACE INTO taxa_lucro (categoria, marketplace, taxa, lucro, arredondamento)
            VALUES (?, ?, ?, ?, ?)
        """, (r['Categoria'], r['Name'], r['Taxa_num'], r['Lucro_num'], int(r['Arredondamento'])))

    # --- PRODUTO (shipping + categoria) ---
    print("  📥 Lendo Produto.xlsx (shipping cost)...")
    produto_df = pd.read_excel(INPUT / "Produto.xlsx")
    produto_df.columns = produto_df.columns.str.strip()
    produto_df['Código CM'] = produto_df['Código CM'].astype(str).str.strip()
    shipping_map = {r['Código CM']: safe_float(r.get('Shipping Cost'))
                    for _, r in produto_df.iterrows()}
    categoria_map = {r['Código CM']: str(r.get('Descrição Categoria', ''))
                     for _, r in produto_df.iterrows()}

    # Atualiza shipping_cost nos produtos
    for sku, ship in shipping_map.items():
        if ship is not None:
            cur.execute("UPDATE produtos SET shipping_cost = ? WHERE sku_principal = ?", (ship, sku))

    # --- SALDOS ---
    print("  📥 Lendo Saldos_de_Estoque.xlsx...")
    est_df = pd.read_excel(INPUT / "Saldos_de_Estoque.xlsx")
    est_df.columns = est_df.columns.str.strip()
    est_df['Código HDS'] = est_df['Código HDS'].astype(str).str.strip()
    est_df['Estoque Atual'] = pd.to_numeric(est_df['Estoque Atual'], errors='coerce').fillna(0)
    est_df.loc[est_df['Estoque Atual'] < 0, 'Estoque Atual'] = 0
    local_map = est_df[['Cód. Local', 'Local']].drop_duplicates().set_index('Cód. Local')['Local'].to_dict()

    # --- TABELAS DE CUSTO ---
    print("  📥 Lendo tabelas de custo Qualy Air...")
    all_prices = []
    for fname in PRICE_FILES:
        path = INPUT / fname
        if not path.exists():
            continue
        try:
            df = pd.read_excel(path)
            df.columns = df.columns.str.strip()
            if 'Código CM' not in df.columns:
                continue
            df['Código CM'] = df['Código CM'].astype(str).str.strip()
            df['Preço'] = pd.to_numeric(df['Preço'], errors='coerce')
            df['Local'] = pd.to_numeric(df['Local'], errors='coerce')
            df = df[df['Preço'].notna() & (df['Preço'] > 0) & df['Local'].notna()][['Código CM', 'Preço', 'Local']]
            all_prices.append(df)
        except Exception as e:
            print(f"     ⚠️  Erro em {fname}: {e}")

    if not all_prices:
        print("❌ Nenhuma tabela de custo encontrada")
        return

    prices = pd.concat(all_prices, ignore_index=True)
    prices['Local_Name'] = prices['Local'].map(local_map)
    prices = prices[prices['Local_Name'].notna()]

    # Best WITH stock (>= 2)
    est_valid = est_df[est_df['Estoque Atual'] >= 2][['Código HDS', 'Cód. Local']]
    merged_stock = prices.merge(est_valid, left_on=['Código CM', 'Local'],
                                right_on=['Código HDS', 'Cód. Local'], how='inner')
    merged_stock['Priority'] = merged_stock['Local_Name'].map(PRIORITY_MAP).fillna(99).astype(int)
    best_stock = (merged_stock.sort_values(['Código CM', 'Preço', 'Priority'])
                  .groupby('Código CM').first().reset_index()[['Código CM', 'Preço', 'Local_Name']])
    best_stock.columns = ['sku', 'custo', 'fornecedor']
    best_stock_map = {r['sku']: r for _, r in best_stock.iterrows()}

    # Best WITHOUT stock (reference)
    prices['Priority'] = prices['Local_Name'].map(PRIORITY_MAP).fillna(99).astype(int)
    best_any = (prices.sort_values(['Código CM', 'Preço', 'Priority'])
                .groupby('Código CM').first().reset_index()[['Código CM', 'Preço', 'Local_Name']])
    best_any.columns = ['sku', 'custo', 'fornecedor']
    best_any_map = {r['sku']: r for _, r in best_any.iterrows()}

    skus_with_price = set(prices['Código CM'].unique())
    skus_with_stock = set(best_stock['sku'])

    # --- CALCULAR PREÇOS ---
    print("  🧮 Calculando preços...")
    cur.execute("DELETE FROM precificacao")

    # Busca todos os produtos
    produtos = cur.execute("SELECT cod_product, sku_principal FROM produtos").fetchall()

    inseridos = 0
    for cod, sku_principal in produtos:
        # Status
        if sku_principal in skus_with_stock:
            status = 'OK'
            best = best_stock_map[sku_principal]
            tem_estoque = 1
        elif sku_principal in skus_with_price:
            status = 'Estoque Insuficiente'
            best = best_any_map[sku_principal]
            tem_estoque = 0
        else:
            status = 'Sem Preço na Tabela'
            cur.execute("""
                INSERT OR REPLACE INTO precificacao (cod_product, status, categoria, tem_estoque)
                VALUES (?, ?, ?, 0)
            """, (cod, status, categoria_map.get(sku_principal, '')))
            inseridos += 1
            continue

        custo = float(best['custo'])
        fornecedor = str(best['fornecedor'])
        shipping = shipping_map.get(sku_principal)
        categoria = categoria_map.get(sku_principal, '')

        precos = {}
        if shipping is not None:
            for mkp, col in MKP_COLS.items():
                key = (categoria, mkp)
                if key not in taxa_dict:
                    continue
                taxa, lucro, arred = taxa_dict[key]
                margem = 1 - (taxa + lucro)
                if margem <= 0:
                    continue
                raw = (custo + shipping) / margem
                precos[col] = round(round_price(raw, arred), 2)

        cur.execute("""
            INSERT OR REPLACE INTO precificacao
            (cod_product, status, categoria, shipping_cost, fornecedor, custo, tem_estoque,
             preco_stock_ac, preco_qualy_air, preco_shopify, preco_walmart, preco_amazon, preco_forceparts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cod, status, categoria, shipping, fornecedor, round(custo, 2), tem_estoque,
            precos.get('preco_stock_ac'), precos.get('preco_qualy_air'),
            precos.get('preco_shopify'), precos.get('preco_walmart'),
            precos.get('preco_amazon'), precos.get('preco_forceparts')
        ))
        inseridos += 1

    conn.commit()
    conn.close()
    print(f"✅ Precificação calculada para {inseridos} produtos")


if __name__ == "__main__":
    criar_tabelas()
    importar()
