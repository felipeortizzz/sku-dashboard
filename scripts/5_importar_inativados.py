"""
5_importar_inativados.py
Marca os produtos inativados no banco de dados.
"""

import pandas as pd
from pathlib import Path
from schema import get_connection, criar_tabelas

INPUT = Path(__file__).parent.parent / "data" / "input"


def importar():
    arquivo = INPUT / "INATIVADOS.xlsx"
    if not arquivo.exists():
        print(f"⚠️  INATIVADOS.xlsx não encontrado, pulando...")
        return

    print("  📥 Lendo INATIVADOS.xlsx...")
    df = pd.read_excel(arquivo)
    df['SKU'] = df['SKU'].astype(str).str.strip()
    df['Sku Supplier'] = df['Sku Supplier'].astype(str).str.strip()

    paused_skus = set(df['SKU'].str.upper()) | set(df['Sku Supplier'].str.upper())

    conn = get_connection()
    cur = conn.cursor()

    # Reseta todos primeiro
    cur.execute("UPDATE produtos SET inativado = 0")

    # Busca todos os produtos e seus equivalentes
    produtos = cur.execute("SELECT cod_product, sku_principal FROM produtos").fetchall()
    equiv_rows = cur.execute("SELECT cod_product, sku_supplier FROM equivalentes").fetchall()

    # Monta mapa de equivalentes
    equiv_map = {}
    for cod, sku in equiv_rows:
        equiv_map.setdefault(cod, []).append(sku.upper())

    marcados = 0
    for cod, sku_principal in produtos:
        is_paused = sku_principal.upper() in paused_skus
        if not is_paused:
            for eq_sku in equiv_map.get(cod, []):
                if eq_sku in paused_skus:
                    is_paused = True
                    break
        if is_paused:
            cur.execute("UPDATE produtos SET inativado = 1 WHERE cod_product = ?", (cod,))
            marcados += 1

    conn.commit()
    conn.close()
    print(f"✅ {marcados} produtos marcados como inativados")


if __name__ == "__main__":
    criar_tabelas()
    importar()
