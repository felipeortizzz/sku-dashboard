"""
1_importar_produtos.py
Importa a base Produtos_Principais_e_Equivalentes.xlsx para o banco SQLite.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from schema import get_connection, criar_tabelas

INPUT = Path(__file__).parent.parent / "data" / "input"


def importar():
    arquivo = INPUT / "Produtos_Principais_e_Equivalentes.xlsx"
    if not arquivo.exists():
        print(f"❌ Arquivo não encontrado: {arquivo}")
        return

    print("📦 Lendo Produtos_Principais_e_Equivalentes.xlsx...")
    df = pd.read_excel(arquivo, header=1)
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)

    cols = ['Cód. Product', 'SKU', 'PRODUCT', 'CATEGORY', 'Partner',
            'Price', 'Sku Supplier', 'Product Supplier', 'Supplier SUP']
    df = df[cols]
    for c in cols:
        df[c] = df[c].fillna('').astype(str).str.strip()
    df = df[df['Cód. Product'] != '']

    conn = get_connection()
    cur = conn.cursor()

    # Limpa tabelas antes de reimportar
    cur.execute("DELETE FROM equivalentes")
    cur.execute("DELETE FROM produtos")

    produtos_inseridos = 0
    equiv_inseridos = 0

    for cod, grupo in df.groupby('Cód. Product'):
        sku_principal = grupo['SKU'].iloc[0]
        nome = grupo['PRODUCT'].iloc[0]
        categoria = grupo['CATEGORY'].iloc[0]

        cur.execute("""
            INSERT OR REPLACE INTO produtos (cod_product, sku_principal, nome, categoria)
            VALUES (?, ?, ?, ?)
        """, (cod, sku_principal, nome, categoria))
        produtos_inseridos += 1

        for _, row in grupo.iterrows():
            sku_sup = row['Sku Supplier']
            supplier = row['Supplier SUP']
            partner = row['Partner']
            if sku_sup and sku_sup != 'nan':
                cur.execute("""
                    INSERT INTO equivalentes (cod_product, sku_supplier, supplier, partner)
                    VALUES (?, ?, ?, ?)
                """, (cod, sku_sup, supplier, partner))
                equiv_inseridos += 1

    conn.commit()
    conn.close()
    print(f"✅ {produtos_inseridos} produtos importados")
    print(f"✅ {equiv_inseridos} equivalentes importados")


if __name__ == "__main__":
    criar_tabelas()
    importar()
