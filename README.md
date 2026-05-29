# 📊 Analista Financeiro Pessoal

Sistema de análise financeira automatizada para carteiras de investimento. Processa extratos da B3 e gera análises técnicas e fundamentalistas de ativos em tempo real.

## ✨ Características

- **Parser B3**: Lê extratos Excel da B3 e classifica ativos automaticamente
- **Análise Multiclasse**: Suporta FIIs, ações, ETFs, BDRs, Tesouro Direto e renda fixa privada
- **Indicadores Técnicos**: RSI, MACD, Bollinger Bands, performance histórica
- **Pesquisa de Dados**: Integração com yfinance para dados em tempo real
- **Relatórios JSON**: Salva análises estruturadas para processamento posterior
- **Testes Completos**: 49 testes unitários com pytest

## 📋 Requisitos

- Python 3.8+
- pip

## 🚀 Instalação

```bash
git clone <repo>
cd analista-financeiro

# Instalar dependências
pip install -r requirements.txt

# (Opcional) Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

## 📖 Como Usar

### 1. Preparar arquivo de extrato

Exporte seu extrato da B3 em formato Excel (.xlsx ou .xls) com as colunas:
- **PRODUTO**: Nome ou ticker do ativo
- **QUANTIDADE**: Quantidade de cotas/ações
- **PREÇO MÉDIO**: Preço médio de aquisição
- **VALOR ATUALIZADO**: Valor atual em reais

### 2. Executar análise

```bash
python3 main.py seu_extrato_b3.xlsx
```

**Saída:**
- Console: Resumo da carteira e distribuição por classe
- `data/carteira.json`: Carteira estruturada
- `data/analise_completa.json`: Análise completa com todos os dados

### 3. Exemplo

```bash
python3 main.py extrato_fevereiro_2025.xlsx
```

```
📊 Iniciando análise da carteira...
   Arquivo: extrato_fevereiro_2025.xlsx

=== CARTEIRA ESTRUTURADA ===
Total de ativos: 5

FII (1 ativo(s)):
  - HGLG11 | Qtd: 100 | Valor: R$ 15050.0

ACAO_BR (2 ativo(s)):
  - PETR4 | Qtd: 50 | Valor: R$ 1265.0
  - ITUB4 | Qtd: 30 | Valor: R$ 2400.0

TESOURO_SELIC (2 ativo(s)):
  - SELIC | Qtd: 1000 | Valor: R$ 100000.0

📈 Analisando FII...
   [1/5] HGLG11... ✓

...

✅ Análise salva em data/analise_completa.json
```

## 📁 Estrutura do Projeto

```
analista-financeiro/
├── main.py                    # Orquestrador principal
├── tools/
│   ├── parser_b3.py          # Parser de extratos B3
│   └── asset_research.py     # Pesquisa de dados de ativos
├── tests/
│   ├── conftest.py           # Fixtures do pytest
│   ├── test_parser_b3.py     # Testes do parser (24 testes)
│   ├── test_asset_research.py # Testes de pesquisa (15 testes)
│   └── test_main.py          # Testes de orquestração (10 testes)
├── data/
│   ├── carteira.json         # Carteira estruturada (gerado)
│   └── analise_completa.json # Análise completa (gerado)
├── requirements.txt          # Dependências Python
├── .env.example              # Variáveis de ambiente (template)
├── .gitignore               # Arquivos ignorados pelo git
├── pytest.ini               # Configuração do pytest
└── README.md                # Este arquivo
```

## 🔧 Componentes

### `main.py`
Orquestra o fluxo completo:
1. Parseia arquivo Excel
2. Para cada ativo, busca dados via yfinance
3. Consolida resultado em JSON

**Funções:**
- `analisar_carteira_completa(arquivo)` — Análise completa
- `gerar_resumo(carteira, analises)` — Gera resumo consolidado
- `salvar_resultado(resultado)` — Salva em JSON

### `tools/parser_b3.py`
Lê e classifica ativos do extrato B3.

**Funções principais:**
- `ler_extrato_b3(caminho)` — Lê arquivo Excel
- `classificar_ativo(produto)` — Classifica por ticker/descricao
- `organizar_por_classe(carteira)` — Agrupa por classe
- `resumo_carteira(carteira)` — Gera texto resumo

**Classes suportadas:**
- FII (Fundos Imobiliários)
- ACAO_BR (Ações brasileiras)
- BDR (Brazilian Depositary Receipts)
- ETF_BR (ETFs brasileiros)
- TESOURO_SELIC, TESOURO_IPCA, TESOURO_PREFIXADO
- RENDA_FIXA_PRIVADA (CDB, LCI, LCA, CRI, CRA, Debêntures, FIDC)
- FUNDO (Fundos de investimento)

### `tools/asset_research.py`
Pesquisa dados de ativos via yfinance.

**Classes:**
- `PesquisadorAtivo` — Classe principal com métodos específicos por classe

**Métodos públicos:**
- `analisar_ativo(ticker, classe)` — Análise completa
- `calcular_indicadores(ticker)` — Indicadores técnicos
- `comparar_com_benchmark(ticker, benchmark)` — Comparação com benchmark

**Indicadores disponíveis:**
- SMA (20, 50, 200)
- RSI (14)
- MACD
- Bollinger Bands
- Volatilidade
- Dividend Yield
- Performance

## 🧪 Testes

### Executar todos os testes
```bash
python3 -m pytest tests/ -v
```

### Executar teste específico
```bash
python3 -m pytest tests/test_parser_b3.py -v
python3 -m pytest tests/test_asset_research.py::TestIndicadores -v
```

### Cobertura de código
```bash
python3 -m pytest tests/ --cov=tools --cov=main --cov-report=html
```

### Modo quiet
```bash
python3 -m pytest tests/ -q
```

**Estatísticas:**
- 49 testes total
- 24 testes para parser
- 15 testes para pesquisa
- 10 testes para orquestração
- ✅ 100% passando

## 📊 Formato de Saída

### `data/carteira.json`
Estrutura normalizada dos ativos:
```json
{
  "FII": [
    {
      "ticker": "HGLG11",
      "descricao": "HGLG11 FUNDO INV IMOB",
      "classe": "FII",
      "quantidade": 100,
      "preco_medio": 150.5,
      "valor_total": 15050.0
    }
  ]
}
```

### `data/analise_completa.json`
Análise consolidada com dados de cada ativo:
```json
{
  "timestamp": "2025-02-28T14:30:00",
  "arquivo_origem": "extrato.xlsx",
  "carteira_estruturada": { ... },
  "analises": {
    "FII": [
      {
        "ticker": "HGLG11",
        "classe": "FII",
        "timestamp": "2025-02-28T14:30:05",
        "dados": {
          "cotacao_atual": 150.50,
          "dividend_yield_12m": 8.5,
          "liquidez_media": 1250000
        }
      }
    ]
  },
  "resumo": {
    "total_classes": 3,
    "total_ativos": 5,
    "distribuicao_por_classe": { ... },
    "alertas": []
  }
}
```

## ⚙️ Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e customize:

```bash
cp .env.example .env
```

**Opções:**
- `MOEDA_PADRAO` — Moeda padrão (BRL)
- `PERIODO_ANALISE` — Período de análise em dias (365)
- `TIMEOUT_REQUISICOES` — Timeout para API em segundos (10)
- `DEBUG` — Modo debug (False/True)

## 🚦 Exemplos de Uso

### Analisar carteira mensal
```bash
python3 main.py extratos/fevereiro_2025.xlsx
```

### Processar múltiplos extratos
```bash
for arquivo in extratos/*.xlsx; do
    python3 main.py "$arquivo"
done
```

### Com testes antes de rodar
```bash
python3 -m pytest tests/ -q && python3 main.py extrato.xlsx
```

## 📈 Próximas Features

- [ ] Dashboard interativo (Streamlit/FastAPI)
- [ ] Integração com Google Sheets para relatório automático
- [ ] Alertas por email/Telegram
- [ ] Histórico de carteira (comparação temporal)
- [ ] Simulações de cenários (Monte Carlo)
- [ ] Integração com API Tesouro Direto
- [ ] Análise de correlação entre ativos
- [ ] Recomendações baseadas em perfil

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip install -r requirements.txt
```

### "Arquivo não encontrado"
Verifique se o arquivo Excel existe e está no caminho correto:
```bash
ls -la seu_extrato.xlsx
```

### "Erro ao ler arquivo Excel"
Certifique-se que o arquivo:
- Tem extensão .xlsx ou .xls
- Contém as colunas: PRODUTO, QUANTIDADE, PREÇO MÉDIO, VALOR ATUALIZADO
- Não tem linhas vazias no início

## 📝 Licença

Projeto pessoal para análise financeira.

## 🤝 Contribuições

Para melhorias ou correções, abra uma issue ou PR.

---

**Última atualização:** Fevereiro 2025
