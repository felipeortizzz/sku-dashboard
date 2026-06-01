"""
3_importar_fornecedores.py
Importa estoque e preços de todos os fornecedores.
"""

import pandas as pd
import json
import math
from pathlib import Path
from schema import get_connection, criar_tabelas

INPUT = Path(__file__).parent.parent / "data" / "input"


def safe_float(v):
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 2)
    except:
        return None


def safe_int(v):
    try:
        f = float(v)
        return 0 if math.isnan(f) else int(f)
    except:
        return 0


def upsert(cur, sku, supplier, preco, quantidade, warehouses=None, localizacao=None):
    sku = str(sku).strip()
    if not sku or sku.upper() == 'NAN':
        return
    wh_json = json.dumps(warehouses) if warehouses else None
    cur.execute("""
        INSERT OR REPLACE INTO fornecedor_dados (sku, supplier, preco, quantidade, warehouses, localizacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sku, supplier, preco, quantidade, wh_json, localizacao))


def importar():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM fornecedor_dados")

    # GPD
    f = INPUT / "GPD.csv"
    fp = INPUT / "GPD__Prices.xlsx"
    if f.exists():
        print("  📥 GPD...")
        df = pd.read_csv(f, header=None, names=['PART', 'QTY'])
        price_map = {}
        if fp.exists():
            dfp = pd.read_excel(fp)[['GPD Part Number', '01.26.26.3A']]
            dfp.columns = ['PART', 'PRICE']
            price_map = {str(r['PART']).strip(): safe_float(r['PRICE']) for _, r in dfp.iterrows()}
        for _, r in df.iterrows():
            upsert(cur, r['PART'], 'GPD', price_map.get(str(r['PART']).strip()), safe_int(r['QTY']))
        print(f"     ✅ {len(df)} registros")

    # UAC
    f = INPUT / "UAC.csv"
    fp = INPUT / "UAC__Prices.xlsx"
    if f.exists():
        print("  📥 UAC...")
        df = pd.read_csv(f)
        price_map = {}
        if fp.exists():
            dfp = pd.read_excel(fp)
            dfp.columns = ['PART', 'PRICE']
            price_map = {str(r['PART']).strip(): safe_float(r['PRICE']) for _, r in dfp.iterrows()}
        for _, r in df.iterrows():
            upsert(cur, r['Part'], 'UAC', price_map.get(str(r['Part']).strip()), safe_int(r['Available Quantity']))
        print(f"     ✅ {len(df)} registros")

    # DNA
    f = INPUT / "DNA.csv"
    fp = INPUT / "DNA__Prices.xlsx"
    if f.exists():
        print("  📥 DNA...")
        df = pd.read_csv(f)
        price_map = {}
        if fp.exists():
            dfp = pd.read_excel(fp)[['SKU', 'PRICE (3)']]
            dfp.columns = ['SKU', 'PRICE']
            price_map = {str(r['SKU']).strip(): safe_float(r['PRICE']) for _, r in dfp.iterrows()}
        for _, r in df.iterrows():
            sku = str(r['SKU']).strip()
            wh = {c[5:-1].upper(): safe_int(r[c])
                  for c in ['QTY (ca)', 'QTY (tx)', 'QTY (nj)', 'QTY (ga)', 'QTY (il)']
                  if pd.notna(r[c])}
            upsert(cur, sku, 'DNA', price_map.get(sku), sum(wh.values()), wh)
        print(f"     ✅ {len(df)} registros")

    # PBI
    f = INPUT / "PBI.csv"
    if f.exists():
        print("  📥 PBI...")
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            wh = {'CA': str(r['CA WAREHOUSE']), 'VA': str(r['VA WAREHOUSE']), 'TX': str(r['TX WAREHOUSE'])}
            upsert(cur, r['PART#'], 'PBI', safe_float(r['PRICE']), None, wh)
        print(f"     ✅ {len(df)} registros")

    # AGILITY
    f = INPUT / "AGI.csv"
    if f.exists():
        print("  📥 AGILITY...")
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            upsert(cur, r['PART#'], 'AGILITY', safe_float(r['PRICE']), safe_int(r['TX']))
        print(f"     ✅ {len(df)} registros")

    # SUNBELT
    f = INPUT / "SB.csv"
    if f.exists():
        print("  📥 SUNBELT...")
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            upsert(cur, r['SKU'], 'SUNBELT', safe_float(r['Price']), safe_int(r['Quantity']))
        print(f"     ✅ {len(df)} registros")

    # APC
    f = INPUT / "APC.xlsx"
    if f.exists():
        print("  📥 APC...")
        df = pd.read_excel(f)
        for _, r in df.iterrows():
            upsert(cur, r['Vendor Part #'], 'APC', None, safe_int(r['Quantity Available for Purchase']),
                   localizacao=str(r.get('Branch Location', '')))
        print(f"     ✅ {len(df)} registros")

    # KCA
    f = INPUT / "KCA.xlsx"
    fp = INPUT / "KCA__Prices.xlsx"
    if f.exists():
        print("  📥 KCA...")
        df = pd.read_excel(f)
        price_map = {}
        if fp.exists():
            dfp = pd.read_excel(fp)[['Manufacturer Part Number', 'Price']]
            dfp.columns = ['PART', 'PRICE']
            price_map = {str(r['PART']).strip(): safe_float(r['PRICE']) for _, r in dfp.iterrows()}
        for _, r in df.iterrows():
            part = str(r['Item Code']).strip()
            upsert(cur, part, 'KCA', price_map.get(part), safe_int(r['Total']))
        print(f"     ✅ {len(df)} registros")

    # AUTOBEST
    f = INPUT / "AUB.csv"
    fp = INPUT / "AUB__Prices.xlsx"
    if f.exists():
        print("  📥 AUTOBEST...")
        df = pd.read_csv(f)
        price_map = {}
        if fp.exists():
            dfp = pd.read_excel(fp)[['AUB#', 2025]]
            dfp.columns = ['PART', 'PRICE']
            price_map = {str(r['PART']).strip(): safe_float(r['PRICE']) for _, r in dfp.iterrows()}
        for _, r in df.iterrows():
            part = str(r['Product/Service Name']).strip()
            upsert(cur, part, 'AUTOBEST', price_map.get(part), safe_int(r['Quantity On Hand']))
        print(f"     ✅ {len(df)} registros")

    # RANSHU
    f = INPUT / "RN.csv"
    if f.exists():
        print("  📥 RANSHU...")
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            wh = {c: safe_int(r[c]) for c in ['NV', 'TX', 'PA', 'FL'] if pd.notna(r[c])}
            upsert(cur, r['PART#'], 'RANSHU', safe_float(r['PRICE']), sum(wh.values()), wh)
        print(f"     ✅ {len(df)} registros")

    conn.commit()
    conn.close()
    print("\n✅ Fornecedores importados com sucesso")


if __name__ == "__main__":
    criar_tabelas()
    importar()
