"""
2_importar_mercados.py
Importa preços dos 6 marketplaces: Stock, Amazon, Qualy, AmericanForce, Shopify, Walmart.
"""

import pandas as pd
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


def importar_ebay(arquivo, marketplace):
    path = INPUT / arquivo
    if not path.exists():
        print(f"  ⚠️  {arquivo} não encontrado, pulando...")
        return []
    df = pd.read_csv(path)[['Custom label (SKU)', 'Current price', 'Available quantity']]
    df.columns = ['sku', 'preco', 'quantidade']
    df['sku'] = df['sku'].astype(str).str.strip()
    df['marketplace'] = marketplace
    return df.to_dict('records')


def importar_amazon():
    path = INPUT / "Amazon.xlsx"
    if not path.exists():
        print("  ⚠️  Amazon.xlsx não encontrado, pulando...")
        return []
    df = pd.read_excel(path)[['seller-sku', 'price', 'quantity']]
    df.columns = ['sku', 'preco', 'quantidade']
    df['sku'] = df['sku'].astype(str).str.strip()
    df['marketplace'] = 'Amazon'
    return df.to_dict('records')


def importar_shopify():
    path = INPUT / "Shopify.csv"
    if not path.exists():
        print("  ⚠️  Shopify.csv não encontrado, pulando...")
        return []
    df = pd.read_csv(path)
    df['SKU'] = df['SKU'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()
    rows = []
    for _, r in df.iterrows():
        rows.append({
            'sku': r['SKU'],
            'marketplace': 'Shopify',
            'preco': safe_float(r['Price']),
            'quantidade': None,
            'preco_compare': safe_float(r.get('Compare-at Price'))
        })
    return rows


def importar_walmart():
    path = INPUT / "Walmart.csv"
    if not path.exists():
        print("  ⚠️  Walmart.csv não encontrado, pulando...")
        return []
    df = pd.read_csv(path)
    df['SKU'] = df['SKU'].astype(str).str.strip()
    rows = []
    for _, r in df.iterrows():
        rows.append({
            'sku': r['SKU'],
            'marketplace': 'Walmart',
            'preco': safe_float(r['Price']),
            'quantidade': None,
            'buy_box': safe_float(r.get('Buy Box Item Price')),
            'status': str(r.get('Publish Status', '')).strip()
        })
    return rows


def importar():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM marketplace_precos")

    total = 0
    fontes = [
        ('Stock.csv', 'Stock'),
        ('Qualy.csv', 'Qualy'),
        ('AmericanForce.csv', 'AmericanForce'),
    ]

    for arquivo, mp in fontes:
        print(f"  📥 Importando {mp}...")
        rows = importar_ebay(arquivo, mp)
        for r in rows:
            cur.execute("""
                INSERT OR REPLACE INTO marketplace_precos (sku, marketplace, preco, quantidade)
                VALUES (?, ?, ?, ?)
            """, (r['sku'], r['marketplace'], safe_float(r.get('preco')), safe_int(r.get('quantidade'))))
        total += len(rows)
        print(f"     ✅ {len(rows)} registros")

    print("  📥 Importando Amazon...")
    rows = importar_amazon()
    for r in rows:
        cur.execute("""
            INSERT OR REPLACE INTO marketplace_precos (sku, marketplace, preco, quantidade)
            VALUES (?, ?, ?, ?)
        """, (r['sku'], r['marketplace'], safe_float(r.get('preco')), safe_int(r.get('quantidade'))))
    total += len(rows)
    print(f"     ✅ {len(rows)} registros")

    print("  📥 Importando Shopify...")
    rows = importar_shopify()
    for r in rows:
        cur.execute("""
            INSERT OR REPLACE INTO marketplace_precos (sku, marketplace, preco, quantidade, preco_compare)
            VALUES (?, ?, ?, ?, ?)
        """, (r['sku'], r['marketplace'], r.get('preco'), None, r.get('preco_compare')))
    total += len(rows)
    print(f"     ✅ {len(rows)} registros")

    print("  📥 Importando Walmart...")
    rows = importar_walmart()
    for r in rows:
        cur.execute("""
            INSERT OR REPLACE INTO marketplace_precos (sku, marketplace, preco, quantidade, buy_box, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (r['sku'], r['marketplace'], r.get('preco'), None, r.get('buy_box'), r.get('status')))
    total += len(rows)
    print(f"     ✅ {len(rows)} registros")

    conn.commit()
    conn.close()
    print(f"\n✅ Total: {total} registros de marketplace importados")


if __name__ == "__main__":
    criar_tabelas()
    importar()
