"""
gerar_json.py
Gera arquivos .json simples na pasta frontend/data/
Execute: python scripts/gerar_json.py
"""

import json, sqlite3, pandas as pd, math
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "db" / "sku_dashboard.db"
INPUT   = Path(__file__).parent.parent / "data" / "input"
OUTPUT  = Path(__file__).parent.parent / "frontend" / "data"
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
sup_data = {}
for sku, supplier, preco, qtd, wh_json, loc in cur.execute(
    "SELECT sku, supplier, preco, quantidade, warehouses, localizacao FROM fornecedor_dados"
).fetchall():
    k = sku.upper()
    if k not in sup_data: sup_data[k] = []
    e = {'s': supplier}
    if preco is not None: e['p'] = round(preco, 2)
    if qtd is not None: e['q'] = int(qtd)
    if wh_json:
        try: e['w'] = json.loads(wh_json)
        except: pass
    if loc and loc not in ('', 'nan', 'None'): e['loc'] = loc
    sup_data[k].append(e)
save(sup_data, OUTPUT / "suppliers.json")

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

# TAXA
try:
    taxa = {}
    for cat, mp_name, t, l, a in cur.execute(
        "SELECT categoria, marketplace, taxa, lucro, arredondamento FROM taxa_lucro"
    ).fetchall():
        if cat not in taxa: taxa[cat] = {}
        taxa[cat][mp_name] = {'t': round(t,4), 'l': round(l,4), 'a': int(a)}
    save(taxa, OUTPUT / "taxa.json")
except Exception as e:
    print(f"  ⚠️  taxa.json: {e}")

conn.close()

# ── SALES (lê direto do arquivo xlsx) ──
CHANNEL_MAP = {
    'AmazonUS':        'Amazon',
    'eBay - Qualy':    'eBay Qualy',
    'eBay - Stock':    'eBay Stock',
    'eBay - American': 'Am. Force',
    'Walmart':         'Walmart',
    'Site':            'Shopify',
    'B2B':             'B2B',
    'B2C':             'B2C',
}

sales_file = None
for name in ['CONSULTA_PORTAIS_COMPRA_VENDA_-_PRODUTOS.xlsx', 'vendas.xlsx', 'Vendas.xlsx']:
    p = INPUT / name
    if p.exists():
        sales_file = p
        break

if not sales_file:
    print("  ⚠️  sales.json: arquivo de vendas não encontrado em data/input/")
    print("       Coloque o arquivo com nome: CONSULTA_PORTAIS_COMPRA_VENDA_-_PRODUTOS.xlsx")
else:
    print(f"\n  📥 Lendo vendas de {sales_file.name}...")
    df = pd.read_excel(sales_file, header=1)
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]

    df['Vlr. Total']      = pd.to_numeric(df['Vlr. Total'],      errors='coerce').fillna(0)
    df['Vlr. Unitário']   = pd.to_numeric(df['Vlr. Unitário'],   errors='coerce').fillna(0)
    df['Qtd. Negociada']  = pd.to_numeric(df['Qtd. Negociada'],  errors='coerce').fillna(0)
    df['Data NF']         = pd.to_datetime(df['Data NF'],        errors='coerce')
    df = df[df['Data NF'].notna()]

    # Somente linhas de venda (TOP começa com 10xx ou 11xx)
    vendas = df[
        df['TOP'].astype(str).str.match(r'^1[01]\d\d$') &
        df['Tipo de Operação'].str.contains('Venda|Marketplaces', na=False, case=False)
    ].copy()

    vendas['canal'] = vendas['Vendedor'].map(CHANNEL_MAP).fillna(vendas['Vendedor'])

    # Índices para compactar o JSON
    cats   = sorted(vendas['Catetoria do Produto'].dropna().unique().tolist())
    canais = sorted(vendas['canal'].dropna().unique().tolist())
    cat_idx   = {c: i for i, c in enumerate(cats)}
    canal_idx = {c: i for i, c in enumerate(canais)}

    rows = []
    for _, r in vendas.iterrows():
        cat   = str(r.get('Catetoria do Produto', '') or '')
        canal = r['canal']
        rows.append([
            str(r.get('Número Único', '')),          # 0 id
            r['Data NF'].strftime('%Y-%m-%d'),        # 1 dia
            canal_idx.get(canal, 0),                  # 2 canal idx
            cat_idx.get(cat, len(cats)),               # 3 cat idx
            str(r.get('Código HDS', '') or '')[:20],  # 4 sku
            str(r.get('Descrição Produto','') or '')[:60],  # 5 desc
            int(r['Qtd. Negociada']),                 # 6 qtd
            round(float(r['Vlr. Unitário']), 2),      # 7 unit
            round(float(r['Vlr. Total']), 2),         # 8 total
        ])

    data = {'cats': cats, 'canais': canais, 'rows': rows}
    save(data, OUTPUT / "sales.json")
    print(f"     {len(rows)} vendas processadas")

print("\n✅ Pronto!")
print("   Agora rode: git add frontend/data/ --force && git commit -m 'atualiza dados' && git push")

# ── TRACKING & RETURNS ──
import json as _json, gzip as _gzip, base64 as _b64
from datetime import datetime as _dt, timedelta as _td
from collections import Counter as _Counter

def _safe_date(v):
    try: return str(_pd.to_datetime(v, utc=True))[:10]
    except: return ''

def _safe_dt(v):
    try: return str(_pd.to_datetime(v, utc=True))[:16]
    except: return ''

def _process_ship(fname):
    path = INPUT / fname
    if not path.exists():
        print(f"  ⚠️  {fname} não encontrado em data/input/")
        return None
    df = _pd.read_excel(path)
    df['order_id'] = df['order_id'].astype(str).str.replace("'","").str.strip()
    df['delivery_time'] = _pd.to_numeric(df['delivery_time'], errors='coerce')
    carriers = sorted(df['slug'].str.split('-').str[0].dropna().unique().tolist())
    statuses = sorted(df['tag'].dropna().unique().tolist())
    stypes   = sorted(df['shipment_type'].dropna().unique().tolist())
    car_idx = {c:i for i,c in enumerate(carriers)}
    sta_idx = {s:i for i,s in enumerate(statuses)}
    sty_idx = {s:i for i,s in enumerate(stypes)}
    is_ret = 'custom_field_item_names' in df.columns
    rows = []
    for _, r in df.iterrows():
        carrier = str(r.get('slug','')).split('-')[0]
        status  = str(r.get('tag',''))
        stype   = str(r.get('shipment_type','') or '')
        row = [
            str(r.get('tracking_number','')),
            str(r.get('order_id','')),
            sta_idx.get(status,0),
            car_idx.get(carrier,0),
            sty_idx.get(stype,len(stypes)),
            _safe_date(r.get('created_at')),
            _safe_date(r.get('shipment_pickup_date')),
            _safe_date(r.get('shipment_delivery_date')),
            _safe_date(r.get('scheduled_delivery_date')),
            int(r['delivery_time']) if _pd.notna(r.get('delivery_time')) else None,
            str(r.get('destination_state','') or '')[:3],
            str(r.get('destination_country_name','') or '')[:20],
            str(r.get('last_checkpoint_message','') or '')[:80],
            str(r.get('subtag',''))[:20],
        ]
        if is_ret:
            row.append(str(r.get('custom_field_item_names','') or '')[:70])
        rows.append(row)
    return {'carriers':carriers,'statuses':statuses,'stypes':stypes,'rows':rows}

_pd = pd  # alias

# Detect filenames (supports multiple naming conventions)
trk_names = ['tracking_01_06_26.xlsx','tracking.xlsx','Tracking.xlsx','TRACKING.xlsx']
ret_names = ['return_01_06_26.xlsx','returns.xlsx','Returns.xlsx','RETURNS.xlsx','return.xlsx']

for names, out_name, label in [(trk_names,'tracking.json','Tracking'),(ret_names,'returns.json','Returns')]:
    found = next((n for n in names if (INPUT/n).exists()), None)
    if found:
        print(f"\n  📥 Processando {label} ({found})...")
        data = _process_ship(found)
        if data:
            save(data, OUTPUT / out_name)
            print(f"     {len(data['rows'])} registros")
    else:
        print(f"  ⚠️  {label}: nenhum arquivo encontrado em data/input/")
        print(f"       Nomes aceitos: {', '.join(names)}")

# ── VELOCITY (vendas últimos 90 dias por SKU) ──
print("\n  📊 Calculando velocity...")
try:
    sales_path = OUTPUT / 'sales.json'
    if sales_path.exists():
        with open(sales_path) as f:
            sales_data = json.loads(f.read())
        
        cutoff = (_dt.now() - _td(days=90)).strftime('%Y-%m-%d')
        vel = {}
        
        # Handle both old format (list of dicts) and new format
        if isinstance(sales_data, list):
            for r in sales_data:
                if r.get('dia','') >= cutoff and r.get('sku'):
                    sku = r['sku']
                    vel[sku] = vel.get(sku,0) + r.get('qtd',0)
        elif isinstance(sales_data, dict) and 'rows' in sales_data:
            for r in sales_data['rows']:
                if len(r) > 6 and r[1] >= cutoff and r[4]:
                    vel[r[4]] = vel.get(r[4],0) + r[6]
        
        top500 = dict(sorted(vel.items(), key=lambda x:-x[1])[:500])
        save(top500, OUTPUT / 'velocity.json')
        print(f"     {len(top500)} SKUs com vendas nos últimos 90 dias")
    else:
        print("  ⚠️  sales.json não encontrado - rode o script de vendas primeiro")
except Exception as e:
    print(f"  ⚠️  velocity: {e}")

# ── GEO (distribuição geográfica das vendas) ──
print("\n  🌎 Calculando distribuição geográfica...")
try:
    # Read from xlsx directly for country/state fields
    sales_files = ['CONSULTA_PORTAIS_COMPRA_VENDA_-_PRODUTOS.xlsx','vendas.xlsx','Vendas.xlsx']
    sales_xl = next((INPUT/n for n in sales_files if (INPUT/n).exists()), None)
    
    if sales_xl:
        df_geo = pd.read_excel(sales_xl, header=1)
        df_geo.columns = df_geo.iloc[0]
        df_geo = df_geo.iloc[1:].reset_index(drop=True)
        df_geo.columns = [str(c).strip() for c in df_geo.columns]
        df_geo['Vlr. Total'] = pd.to_numeric(df_geo['Vlr. Total'], errors='coerce').fillna(0)
        df_geo = df_geo[df_geo['TOP'].astype(str).str.match(r'^1[01]\d\d$', na=False)]
        df_geo = df_geo[df_geo['Tipo de Operação'].str.contains('Venda|Marketplaces', na=False, case=False)]
        
        rev_country = {}
        ord_country = {}
        for _, r in df_geo.iterrows():
            p = str(r.get('País','')).strip()
            if p and p not in ('nan',''):
                rev_country[p] = rev_country.get(p,0) + float(r['Vlr. Total'])
                ord_country[p] = ord_country.get(p,0) + 1
        
        us = df_geo[df_geo['País'].str.contains('United States', na=False, case=False)]
        state_rev = us.groupby('UF')['Vlr. Total'].sum().to_dict()
        state_ord = us.groupby('UF')['Vlr. Total'].count().to_dict()
        
        geo = {
            'countries': {k:round(v,2) for k,v in sorted(rev_country.items(),key=lambda x:-x[1])[:30]},
            'orders_by_country': {k:v for k,v in sorted(ord_country.items(),key=lambda x:-x[1])[:30]},
            'us_states_rev': {str(k):round(float(v),2) for k,v in state_rev.items()},
            'us_states_orders': {str(k):int(v) for k,v in state_ord.items()},
        }
        save(geo, OUTPUT / 'geo.json')
        print(f"     {len(geo['countries'])} países, {len(geo['us_states_rev'])} estados EUA")
    else:
        print("  ⚠️  Base de vendas não encontrada para gerar geo.json")
except Exception as e:
    print(f"  ⚠️  geo: {e}")
