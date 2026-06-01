"""
atualizar_tudo.py
Roda todos os scripts de importação em sequência.
Execute este arquivo sempre que receber novas bases.

Como usar:
  No terminal do VSCode: python scripts/atualizar_tudo.py
"""

import sys
import time
from pathlib import Path

# Garante que os scripts conseguem importar schema.py
sys.path.insert(0, str(Path(__file__).parent))

from schema import criar_tabelas
from importlib import import_module


def rodar(nome, modulo):
    print(f"\n{'='*50}")
    print(f"  {nome}")
    print(f"{'='*50}")
    inicio = time.time()
    try:
        mod = import_module(modulo)
        mod.importar()
        print(f"  ⏱  {time.time() - inicio:.1f}s")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n🚀 SKU Dashboard — Atualização completa")
    print(f"{'='*50}")

    inicio_total = time.time()

    print("\n📁 Criando/verificando banco de dados...")
    criar_tabelas()

    rodar("1/5 — Produtos e Equivalentes",  "1_importar_produtos")
    rodar("2/5 — Marketplaces",             "2_importar_mercados")
    rodar("3/5 — Fornecedores",             "3_importar_fornecedores")
    rodar("4/5 — Precificação",             "4_importar_precificacao")
    rodar("5/5 — Inativados",               "5_importar_inativados")

    print(f"\n{'='*50}")
    print("📤 Exportando dados para o frontend...")
    print(f"{'='*50}")
    from exportar_dados import exportar
    exportar()

    total = time.time() - inicio_total
    print(f"\n{'='*50}")
    print(f"✅ Tudo pronto em {total:.1f}s")
    print(f"   Abra frontend/index.html no seu browser para usar o sistema.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
