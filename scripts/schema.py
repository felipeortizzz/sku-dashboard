"""
schema.py — Define e cria o banco de dados SQLite
Chamado automaticamente pelos scripts de importação.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "db" / "sku_dashboard.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        -- Produtos principais
        CREATE TABLE IF NOT EXISTS produtos (
            cod_product     TEXT PRIMARY KEY,
            sku_principal   TEXT NOT NULL,
            nome            TEXT,
            categoria       TEXT,
            shipping_cost   REAL,
            ativo           INTEGER DEFAULT 1,
            inativado       INTEGER DEFAULT 0
        );

        -- SKUs equivalentes (fornecedores)
        CREATE TABLE IF NOT EXISTS equivalentes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_product     TEXT NOT NULL,
            sku_supplier    TEXT NOT NULL,
            supplier        TEXT,
            partner         TEXT,
            FOREIGN KEY (cod_product) REFERENCES produtos(cod_product)
        );

        -- Índice para busca rápida por qualquer SKU
        CREATE INDEX IF NOT EXISTS idx_equiv_sku
            ON equivalentes(sku_supplier);

        CREATE INDEX IF NOT EXISTS idx_equiv_cod
            ON equivalentes(cod_product);

        -- Preços nos marketplaces
        CREATE TABLE IF NOT EXISTS marketplace_precos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT NOT NULL,
            marketplace     TEXT NOT NULL,
            preco           REAL,
            quantidade      INTEGER,
            preco_compare   REAL,  -- Shopify compare-at
            buy_box         REAL,  -- Walmart buy box
            status          TEXT,  -- Walmart publish status
            UNIQUE(sku, marketplace)
        );

        CREATE INDEX IF NOT EXISTS idx_mp_sku
            ON marketplace_precos(sku);

        -- Estoque e preços dos fornecedores
        CREATE TABLE IF NOT EXISTS fornecedor_dados (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT NOT NULL,
            supplier        TEXT NOT NULL,
            preco           REAL,
            quantidade      INTEGER,
            warehouses      TEXT,  -- JSON string com breakdown por warehouse
            localizacao     TEXT,
            UNIQUE(sku, supplier)
        );

        CREATE INDEX IF NOT EXISTS idx_forn_sku
            ON fornecedor_dados(sku);

        -- Precificação calculada
        CREATE TABLE IF NOT EXISTS precificacao (
            cod_product     TEXT PRIMARY KEY,
            status          TEXT,
            categoria       TEXT,
            shipping_cost   REAL,
            fornecedor      TEXT,
            custo           REAL,
            tem_estoque     INTEGER DEFAULT 0,
            preco_stock_ac      REAL,
            preco_qualy_air     REAL,
            preco_shopify       REAL,
            preco_walmart       REAL,
            preco_amazon        REAL,
            preco_forceparts    REAL,
            FOREIGN KEY (cod_product) REFERENCES produtos(cod_product)
        );

        -- Taxa e lucro por categoria/marketplace
        CREATE TABLE IF NOT EXISTS taxa_lucro (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria       TEXT NOT NULL,
            marketplace     TEXT NOT NULL,
            taxa            REAL,
            lucro           REAL,
            arredondamento  INTEGER,
            UNIQUE(categoria, marketplace)
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Banco de dados criado/verificado com sucesso.")


if __name__ == "__main__":
    criar_tabelas()
