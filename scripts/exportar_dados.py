"""
exportar_dados.py
Lê o banco SQLite e gera os arquivos .json.gz para o frontend.
"""

import json
import gzip
import sqlite3
from pathlib import Path
from schema import get_connection

OUTPUT = Path(__file__).parent.parent / "frontend" / "data"


def exportar():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    print("📤 Exportando dados para o frontend...")

    # --- 1. SKU MAP: qualquer SKU → cod_product ---
    print("  🔑 Gerando mapa de SKUs...")
    sku_map = {}

    rows = cur.execute("SELECT cod_product, sku_principal FROM produtos").fetchall()
    for cod, sku in rows:
        sku_map[sku.upper()] = cod

    rows = cur.execute("SELECT cod_product, sku_supplier FROM equivalentes").fetchall()
    for cod, sku in rows:
        if sku and sku.upper() != 'NAN':
            sku_map[sku.upper()] = cod

    _save(sku_map, OUTPUT / "sku_map.json.gz")
    print(f"     ✅ {len(sku_map)} SKUs mapeados")

    # --- 2. PRODUCTS INDEX: cod_product → dados do produto ---
    print("  📦 Gerando índice de produtos...")
    prod_index = {}

    rows = cur.execute("""
        SELECT cod_product, sku_principal, nome, categoria, shipping_cost, inativado
        FROM produtos
    """).fetchall()

    for cod, sku, nome, cat, ship, inativado in rows:
        prod_index[cod] = {
            'sku': sku,
            'name': nome or '',
            'cat': cat or '',
            'ship': ship,
            'paused': bool(inativado),
            'eq': []
        }

    rows = cur.execute("SELECT cod_product, sku_supplier, supplier FROM equivalentes").fetchall()
    for cod, sku, supplier in rows:
        if cod in prod_index and sku and sku != 'nan':
            prod_index[cod]['eq'].append([sku, supplier or ''])

    _save(prod_index, OUTPUT / "products.json.gz")
    print(f"     ✅ {len(prod_index)} produtos")

    # --- 3. MARKETPLACE PRICES: SKU → [{mp, p, q, ...}] ---
    print("  🛒 Gerando preços de marketplace...")
    mp_data = {}

    rows = cur.execute("""
        SELECT sku, marketplace, preco, quantidade, preco_compare, buy_box, status
        FROM marketplace_precos
    """).fetchall()

    for sku, mp, preco, qtd, compare, buybox, st in rows:
        k = sku.upper()
        if k not in mp_data:
            mp_data[k] = []
        entry = {'mp': mp}
        if preco is not None:
            entry['p'] = round(preco, 2)
        if qtd is not None:
            entry['q'] = int(qtd)
        if compare is not None:
            entry['cp'] = round(compare, 2)
        if buybox is not None:
            entry['bb'] = round(buybox, 2)
        if st and st not in ('', 'nan', 'None'):
            entry['st'] = st
        mp_data[k].append(entry)

    _save(mp_data, OUTPUT / "marketplace.json.gz")
    print(f"     ✅ {len(mp_data)} SKUs com dados de marketplace")

    # --- 4. SUPPLIER DATA: SKU → [{s, p, q, w, loc}] ---
    print("  🏭 Gerando dados de fornecedores...")
    sup_data = {}

    rows = cur.execute("""
        SELECT sku, supplier, preco, quantidade, warehouses, localizacao
        FROM fornecedor_dados
    """).fetchall()

    for sku, supplier, preco, qtd, wh_json, loc in rows:
        k = sku.upper()
        if k not in sup_data:
            sup_data[k] = []
        entry = {'s': supplier}
        if preco is not None:
            entry['p'] = round(preco, 2)
        if qtd is not None:
            entry['q'] = int(qtd)
        if wh_json:
            try:
                entry['w'] = json.loads(wh_json)
            except:
                pass
        if loc and loc not in ('', 'nan', 'None'):
            entry['loc'] = loc
        sup_data[k].append(entry)

    _save(sup_data, OUTPUT / "suppliers.json.gz")
    print(f"     ✅ {len(sup_data)} SKUs com dados de fornecedor")

    # --- 5. PRICING: cod_product → dados de precificação ---
    print("  💰 Gerando precificação...")
    pricing_data = {}

    rows = cur.execute("""
        SELECT cod_product, status, categoria, shipping_cost, fornecedor, custo, tem_estoque,
               preco_stock_ac, preco_qualy_air, preco_shopify, preco_walmart, preco_amazon, preco_forceparts
        FROM precificacao
    """).fetchall()

    for (cod, status, cat, ship, forn, custo, tem_estoque,
         p_stock, p_qualy, p_shopify, p_walmart, p_amazon, p_force) in rows:
        entry = {
            'status': status,
            'cat': cat or '',
            'ship': ship,
            'sup': forn,
            'cost': round(custo, 2) if custo else None,
            'has_stock': bool(tem_estoque),
            'prices': {}
        }
        mp_price_map = {
            'Stock AC': p_stock,
            'QUALY AIR': p_qualy,
            'Qualy Air Shopify': p_shopify,
            'Walmart US': p_walmart,
            'Qualy Air - Amazon US': p_amazon,
            'Ebay-Forceparts': p_force,
        }
        for mkp, val in mp_price_map.items():
            if val is not None:
                entry['prices'][mkp] = round(val, 2)
        pricing_data[cod] = entry

    _save(pricing_data, OUTPUT / "pricing.json.gz")
    print(f"     ✅ {len(pricing_data)} produtos precificados")

    conn.close()
    print("\n✅ Exportação concluída! Arquivos em frontend/data/")


def _save(data, path):
    compressed = gzip.compress(json.dumps(data, separators=(',', ':')).encode())
    with open(path, 'wb') as f:
        f.write(compressed)
    size_kb = len(compressed) // 1024
    print(f"       💾 {path.name}: {size_kb} KB")


if __name__ == "__main__":
    exportar()
