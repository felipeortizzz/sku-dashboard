"""
gerar_json.py
Gera arquivos .json simples na pasta frontend/data/
Execute: python scripts/gerar_json.py
"""

import json, sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "db" / "sku_dashboard.db"
OUTPUT = Path(__file__).parent.parent / "frontend" / "data"
OUTPUT.mkdir(parents=True, exist_ok=True)

def save(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f"  ✅ {path.name}: {path.stat().st_size // 1024} KB")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
print("📤 Gerando arquivos JSON...\n")

# SKU MAP
sku_map = {}
for cod, sku in cur.execute("SELECT cod_product, sku_principal FROM produtos").fetchall():
    sku_map[sku.upper()] = cod
for cod, sku in cur.execute("SELECT cod_product, sku_supplier FROM equivalentes").fetchall():
    if sku and sku.upper() != 'NAN':
        sku_map[sku.upper()] = cod
save(sku_map, OUTPUT / "sku_map.json")

# PRODUCTS
prod = {}
for cod, sku, nome, cat, ship, inativado in cur.execute(
    "SELECT cod_product, sku_principal, nome, categoria, shipping_cost, inativado FROM produtos"
).fetchall():
    prod[cod] = {'sku': sku, 'name': nome or '', 'cat': cat or '', 'ship': ship, 'paused': bool(inativado), 'eq': []}
for cod, sku, sup in cur.execute("SELECT cod_product, sku_supplier, supplier FROM equivalentes").fetchall():
    if cod in prod and sku and sku != 'nan':
        prod[cod]['eq'].append([sku, sup or ''])
save(prod, OUTPUT / "products.json")

# MARKETPLACE
mp = {}
for sku, marketplace, preco, qtd, compare, buybox, st in cur.execute(
    "SELECT sku, marketplace, preco, quantidade, preco_compare, buy_box, status FROM marketplace_precos"
).fetchall():
    k = sku.upper()
    if k not in mp: mp[k] = []
    e = {'mp': marketplace}
    if preco is not None: e['p'] = round(preco, 2)
    if qtd is not None: e['q'] = int(qtd)
    if compare is not None: e['cp'] = round(compare, 2)
    if buybox is not None: e['bb'] = round(buybox, 2)
    if st and st not in ('', 'nan', 'None'): e['st'] = st
    mp[k].append(e)
save(mp, OUTPUT / "marketplace.json")

# SUPPLIERS
sup = {}
for sku, supplier, preco, qtd, wh_json, loc in cur.execute(
    "SELECT sku, supplier, preco, quantidade, warehouses, localizacao FROM fornecedor_dados"
).fetchall():
    k = sku.upper()
    if k not in sup: sup[k] = []
    e = {'s': supplier}
    if preco is not None: e['p'] = round(preco, 2)
    if qtd is not None: e['q'] = int(qtd)
    if wh_json:
        try: e['w'] = json.loads(wh_json)
        except: pass
    if loc and loc not in ('', 'nan', 'None'): e['loc'] = loc
    sup[k].append(e)
save(sup, OUTPUT / "suppliers.json")

# PRICING
pricing = {}
for (cod, status, cat, ship, forn, custo, tem_estoque,
     p_stock, p_qualy, p_shopify, p_walmart, p_amazon, p_force) in cur.execute(
    "SELECT cod_product, status, categoria, shipping_cost, fornecedor, custo, tem_estoque,"
    "preco_stock_ac, preco_qualy_air, preco_shopify, preco_walmart, preco_amazon, preco_forceparts FROM precificacao"
).fetchall():
    e = {'status': status, 'cat': cat or '', 'ship': ship, 'sup': forn,
         'cost': round(custo, 2) if custo else None, 'has_stock': bool(tem_estoque), 'prices': {}}
    for mkp, val in [('Stock AC', p_stock), ('QUALY AIR', p_qualy), ('Qualy Air Shopify', p_shopify),
                     ('Walmart US', p_walmart), ('Qualy Air - Amazon US', p_amazon), ('Ebay-Forceparts', p_force)]:
        if val is not None: e['prices'][mkp] = round(val, 2)
    pricing[cod] = e
save(pricing, OUTPUT / "pricing.json")

conn.close()
print("\n✅ Pronto! Agora rode: git add frontend/data/ --force && git commit -m 'dados json' && git push")
