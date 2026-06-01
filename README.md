# SKU Dashboard

Sistema de consulta de produtos, preços e precificação por marketplace.

---

## Estrutura do Projeto

```
sku_dashboard/
├── data/                        ← Coloque suas bases aqui
│   ├── input/                   ← Arquivos originais (.xlsx / .csv)
│   └── db/
│       └── sku_dashboard.db     ← Banco SQLite (gerado automaticamente)
├── scripts/
│   ├── 1_importar_produtos.py   ← Importa base de produtos e equivalentes
│   ├── 2_importar_mercados.py   ← Importa Stock, Amazon, Qualy, AF, Shopify, Walmart
│   ├── 3_importar_fornecedores.py ← Importa bases dos fornecedores
│   ├── 4_importar_precificacao.py ← Importa TAXA_E_LUCRO, calcula preços
│   ├── 5_importar_inativados.py ← Importa lista de inativados
│   ├── exportar_dados.py        ← Gera os arquivos .json.gz para o frontend
│   └── atualizar_tudo.py        ← Roda todos os scripts de uma vez
├── frontend/
│   └── index.html               ← Abre no browser para usar o sistema
└── README.md
```

---

## ✅ Pré-requisitos

### 1. Instalar Python
- Acesse: https://www.python.org/downloads/
- Baixe a versão **3.10 ou superior**
- Durante a instalação, marque a opção **"Add Python to PATH"**
- Para verificar: abra o terminal e digite `python --version`

### 2. Instalar o VSCode
- Acesse: https://code.visualstudio.com/
- Instale normalmente

### 3. Instalar as bibliotecas necessárias
Abra o terminal no VSCode (`Ctrl + J`) e rode:
```bash
pip install pandas openpyxl
```

---

## 🚀 Como usar pela primeira vez

### Passo 1 — Abrir o projeto no VSCode
1. Abra o VSCode
2. Clique em **File → Open Folder**
3. Selecione a pasta `sku_dashboard`

### Passo 2 — Colocar suas bases na pasta correta
Copie todos os arquivos `.xlsx` e `.csv` para a pasta `data/input/`:

| Arquivo | Descrição |
|---|---|
| `Produtos_Principais_e_Equivalentes.xlsx` | Base principal de produtos |
| `Stock.csv` | eBay Stock |
| `Amazon.xlsx` | Amazon |
| `Qualy.csv` | eBay Qualy |
| `AmericanForce.csv` | American Force |
| `Shopify.csv` | Shopify |
| `Walmart.csv` | Walmart |
| `GPD.csv` + `GPD__Prices.xlsx` | Fornecedor GPD |
| `UAC.csv` + `UAC__Prices.xlsx` | Fornecedor UAC |
| `DNA.csv` + `DNA__Prices.xlsx` | Fornecedor DNA |
| `PBI.csv` | Fornecedor PBI |
| `AGI.csv` | Fornecedor AGI |
| `SB.csv` | Fornecedor Sunbelt |
| `APC.xlsx` | Fornecedor APC |
| `KCA.xlsx` + `KCA__Prices.xlsx` | Fornecedor KCA |
| `AUB.csv` + `AUB__Prices.xlsx` | Fornecedor Autobest |
| `RN.csv` | Fornecedor Ranshu |
| `Qualy_Air_*.xlsx` | Tabelas de custo (todas) |
| `TAXA_E_LUCRO.xlsx` | Taxas e margens por marketplace |
| `Produto.xlsx` | Shipping cost + categorias |
| `Saldos_de_Estoque.xlsx` | Estoque por local |
| `INATIVADOS.xlsx` | Produtos inativados |

### Passo 3 — Importar os dados
No terminal do VSCode, rode:
```bash
python scripts/atualizar_tudo.py
```
Isso vai criar o banco de dados e gerar todos os arquivos para o frontend.
Aguarde — pode levar alguns minutos na primeira vez.

### Passo 4 — Abrir o sistema
1. Vá até a pasta `frontend/`
2. Dê dois cliques em `index.html`
3. O sistema abre no seu browser

---

## 🔄 Como atualizar os dados

Sempre que receber novas bases dos fornecedores:
1. Substitua os arquivos na pasta `data/input/`
2. Rode novamente no terminal:
```bash
python scripts/atualizar_tudo.py
```
3. Recarregue o browser (`F5`)

---

## ❓ Problemas comuns

**"python não é reconhecido"**
→ Reinstale o Python marcando "Add Python to PATH"

**"ModuleNotFoundError: No module named 'pandas'"**
→ Rode `pip install pandas openpyxl` no terminal

**"Arquivo não encontrado"**
→ Verifique se o arquivo está na pasta `data/input/` com o nome exato

**A página abre mas não carrega dados**
→ Rode o `atualizar_tudo.py` primeiro para gerar os dados
