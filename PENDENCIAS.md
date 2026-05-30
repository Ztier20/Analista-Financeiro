# 📋 Pendências — Analista Financeiro

**Status:** v3.1 (Análise Consolidada + Busca Proativa FII Implementadas)
**Data:** 30/05/2026
**Total de Pendências:** 18 itens (26-28 horas de desenvolvimento)

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS (Ao Retomar)

**Prioridade 1 — Dashboard FII (2-3 horas):**
```
Adicionar aba 9 "📋 FII Detalhes" ou expandir "🎯 Ranking":
- Filtro: mostrar apenas FIIs
- Para cada FII (papel vs tijolo):
  ✓ Portfólio de CRIs (tabela com num, duration, indexadores)
  ✓ Vacância estimada (% ocupação com alerta se < 80%)
  ✓ Fluxo de caixa (FFO, payout, sustentabilidade)
  ✓ Patrimônio (crescimento 12m)
  ✓ Liquidez (score 0-10)
- Gráficos: ocupação vs DY, payout ratio, patrimônio timeline

Implementação:
1. Criar função exibir_fii_detalhes() em dashboard.py
2. Adicionar tab9 ao st.tabs()
3. Testar com DEVA11 (papel) + SNAG11 (tijolo)
4. Commit: "Feat: Aba 9 - FII Detalhes no Dashboard"
```

**Prioridade 2 — Ações Brasileiras (3-4 horas):**
```
Próximo no CLAUDE.md:
- Dados trimestrais (DRE, EBITDA, lucro)
- FCF (fluxo de caixa livre)
- Dívida/EBITDA
- Payout ratio

Padrão: copiar estrutura de fii_analytics.py
Arquivo: tools/acoes_analytics.py
```

---

---

## ✅ Implementado (v3.1 — 30/05/2026)

### Core Funcionalidades
- ✅ Parser B3 (8+ tipos de ativos)
- ✅ Macro data (Selic, IPCA, CDI, câmbio via BCB)
- ✅ Scoring 0-10 por classe
- ✅ Recomendações (AUMENTE/MANTENHA/REDUZA/VENDA)
- ✅ Correlação (matriz + diversificação)
- ✅ Sharpe/Sortino (risco ajustado)
- ✅ Análise Consolidada (concentração, alertas) — **NOVO**
- ✅ Busca Proativa FII (liquidez, patrimônio, vacância, CRI, FCF) — **NOVO**

### Entradas/Saídas
- ✅ CLI: `relatorio.py` (análise + markdown com dados proativos FII)
- ✅ Dashboard: 8 abas (Streamlit + Plotly)
- ✅ JSON: carteira estruturada

### Arquivos Novos Esta Sessão
- ✅ `tools/consolidacao.py` (170 linhas)
- ✅ `tools/fii_analytics.py` (550+ linhas)
- ✅ `PENDENCIAS.md` (roadmap completo)
- ✅ Aba 8 "🎯 Consolidada" no dashboard

---

## ⏳ Pendências por Prioridade

### 🔴 Prioridade 1 — Completar CLAUDE.md (Essencial)

#### 1.1 Busca Proativa Detalhada — FII
**Status:** ✅ IMPLEMENTADO (30/05/2026)
**Tempo gasto:** 3.5 horas
**Impacto:** ⭐⭐⭐⭐⭐

Dados faltando segundo CLAUDE.md (linhas 80-90):
```
✅ Implementado:
  - Dividend yield (DY) — via yfinance
  - P/VP — via Brapi (fallback)

❌ Faltando:
  - Vacância física e financeira (% ocupação)
  - Portfólio de CRIs e indexadores (detalhe por ativo subjacente)
  - Fluxo de caixa distribuível vs distribuído
  - Evolução do patrimônio líquido (série temporal)
  - Liquidez diária média (volume médio)
```

**Implementação:** ✅ CONCLUÍDO
- `tools/fii_analytics.py` com 6 funções principais
- Integrado a `asset_research.py` (chamada automática)
- Dados inclusos em `interpretador.py` para análise textual
- Aparece no relatório markdown (CLI)

**Dados recuperados:**
- ✅ Vacância (estimada via DY)
- ✅ Portfólio de CRIs (num, duration, indexadores)
- ✅ Fluxo de caixa distribuível (FFO, payout)
- ✅ Evolução do patrimônio (12 meses)
- ✅ Liquidez diária (volume via yfinance)

**Teste realizado:** DEVA11, MXRF11, SNAG11, BRCR11
- ✅ Dados aparecem no relatório markdown
- ⏳ Ainda faltam no dashboard (próximo passo)

---

#### 1.2 Busca Proativa Detalhada — Ações Brasileiras
**Status:** ⏳ Parcialmente implementado
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐⭐

Dados faltando segundo CLAUDE.md (linhas 92-99):
```
✅ Implementado:
  - P/L, P/VP, DY (via Brapi/yfinance)
  - Beta (volatilidade)
  - Setor

❌ Faltando:
  - Últimos resultados trimestrais (DRE)
    - Receita, EBITDA, lucro líquido
  - Fluxo de caixa livre (FCF)
  - Dívida líquida / EBITDA
  - Payout ratio (dividendos / lucro)
  - Crescimento LPA (EPS growth) histórico
```

**Implementação:**
- Integrar com B3 RI (Relações com Investidor)
- API: Alpha Vantage ou FundRazor para dados fundamentalistas
- Cálculos de índices faltando
- Cache de dados trimestrais

**Teste:** BBDC3, PETR4, VALE3

---

#### 1.3 Busca Proativa Detalhada — Renda Fixa
**Status:** ⏳ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐⭐

Dados faltando segundo CLAUDE.md (linhas 101-107):
```
✅ Implementado:
  - Taxa atual (via BCB ou CDB API)

❌ Faltando:
  - Duration (sensibilidade a taxa de juros)
  - Spread sobre benchmark (CDI ou IPCA)
  - Posição na curva de juros
  - Risco de crédito do emissor
  - Rating de crédito (S&P/Moody's)
  - Liquidez (bid-ask spread)
```

**Implementação:**
- Anbima API para spreads e curva
- BCB para duração de Tesouro
- Web scraping de CDB/LCI ratings
- Cálculo de spread = taxa_ativo - benchmark

**Teste:** TESOURO_IPCA, CDB, LCI

---

#### 1.4 Busca Proativa Detalhada — ETFs
**Status:** ⏳ Parcialmente implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

Dados faltando segundo CLAUDE.md (linhas 109-115):
```
✅ Implementado:
  - Performance 1 ano (via yfinance)
  - Índice subjacente

❌ Faltando:
  - Composição detalhada (top 10 holdings)
  - TER (taxa de administração)
  - AUM (patrimônio total)
  - Comparação com benchmark (beta)
  - Volume médio (liquidez)
```

**Implementação:**
- ETF.com API ou web scraping
- Yahoo Finance para composição
- Cálculo de correlação com benchmark

**Teste:** IVVB11, BOVA11, SPXI11

---

#### 1.5 Busca Proativa Detalhada — REITs
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

Dados segundo CLAUDE.md (linhas 117-123):
```
❌ Todos faltando:
  - FFO por cota (Funds From Operations)
  - Dividend yield
  - Taxa de ocupação (occupancy rate)
  - P/FFO (valuation alternativo)
  - Análise de portfólio (setores, geografias)
```

**Implementação:**
- Integrar yfinance para REITs internacionais
- REIT.com ou Bloomberg para FFO
- Ocupação via relatórios da empresa

**Teste:** O (Realty Income), AMT (American Tower)

---

### 🟠 Prioridade 2 — Ativos Internacionais (Alta Importância)

#### 2.1 Parser B3 Estendido para Internacionais
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐⭐

**Problema:**
- Parser atual só lê B3 (tickers brasileiros: XXXX3, XXXXX11, etc)
- Não suporta tickers internacionais (.US, .CH, etc)
- Falta suporte para REITs, ações gringas, bonds

**Implementação:**
```
Novos tipos no parser:
- ACAO_INTERNACIONAL (ex: AAPL, MSFT)
- REIT_INTERNACIONAL (ex: O, AMT)
- FUNDO_INTERNACIONAL (ex: SPY, QQQ)
- RENDA_FIXA_INTERNACIONAL (ex: TLT, BND)
- CRIPTO (ex: BTC, ETH) — opcional

Input: Usuário cola dados de portfólio internacional
Output: Classificação automática + análise em dólar
```

**Teste:** AAPL, MSFT, BRK.B, O

---

#### 2.2 Análise de Ações Internacionais
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

**Implementação:**
- Valuation em USD (P/L, P/VP, EV/EBITDA)
- Setor e posição em índice (S&P 500, Nasdaq)
- Moeda: impacto de câmbio na rentabilidade em reais
- Fed Funds Rate como contexto
- Dividend yield
- Rating de crédito (para bonds)

**Integração:** yfinance + Alpha Vantage

---

#### 2.3 Análise de REITs Internacionais
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

**Implementação:**
- FFO por cota
- Dividend yield
- Taxa de ocupação
- Localização (setores, geografias)
- Moneda (USD, CAD, EUR) e impacto cambial

---

#### 2.4 Análise de Bonds Internacionais
**Status:** ❌ Não implementado
**Tempo:** 2 horas
**Impacto:** ⭐⭐

**Implementação:**
- Duration
- Yield to Maturity (YTM)
- Grau de investimento (IG vs HY)
- Rating de crédito
- Posição na curva americana

---

### 🟡 Prioridade 3 — Indicadores Macroeconômicos Adicionais

#### 3.1 PIB Brasileiro
**Status:** ❌ Não implementado
**Tempo:** 0.5 hora
**Impacto:** ⭐⭐

**Implementação:**
- BCB Open Data API (série de PIB)
- Crescimento trimestral e anual
- Adicionar ao dashboard (aba Macro)

---

#### 3.2 Fed Funds Rate
**Status:** ❌ Não implementado
**Tempo:** 0.5 hora
**Impacto:** ⭐⭐⭐

**Implementação:**
- FRED API (Federal Reserve Economic Data)
- Taxa atual + histórico 1 ano
- Contexto para ativos internacionais

---

#### 3.3 DXY (Dólar Index)
**Status:** ❌ Não implementado
**Tempo:** 0.5 hora
**Impacto:** ⭐⭐

**Implementação:**
- yfinance (ticker: DXY)
- Impacto no câmbio BRL/USD

---

#### 3.4 Spreads de Crédito
**Status:** ❌ Não implementado
**Tempo:** 1-2 horas
**Impacto:** ⭐⭐

**Implementação:**
- Anbima API (spreads de CDB, debêntures)
- Bloomberg fallback (web scraping)
- Adicionar ao contexto macro

---

#### 3.5 Curva de Juros (DI Futuro)
**Status:** ❌ Não implementado
**Tempo:** 2 horas
**Impacto:** ⭐⭐⭐

**Implementação:**
- B3 API ou Anbima
- Taxa forward (1m, 3m, 6m, 1y, 2y, etc)
- Gráfico de curva
- Análise de inclinação (slope)

---

### 🟢 Prioridade 4 — Automação e Alertas

#### 4.1 Automação de Monitoramento (Watcher)
**Status:** ❌ Não implementado
**Tempo:** 3 horas
**Impacto:** ⭐⭐⭐⭐

**Funcionalidade:**
```
1. Usuário configura pasta para monitorar (ex: ~/Downloads/B3)
2. Sistema monitora novos extratos B3 (.xlsx)
3. Ao detectar novo arquivo:
   - Executa relatorio.py automaticamente
   - Salva em data/relatorios/YYYYMMDD_HH:MM
   - Envia notificação (email ou Telegram)
4. Historiza todos os relatórios para comparação

Arquivo config:
  - Pasta a monitorar
  - Frequência de check (5min, 1h, etc)
  - Email/Telegram para notificações
```

**Implementação:**
- watchdog (Python lib)
- APScheduler para rechecks periódicos
- Email/Telegram via credenciais do usuário

---

#### 4.2 Alertas em Tempo Real
**Status:** ⏳ Parcialmente implementado (consolidação só)
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐⭐

**Tipos de alertas:**
```
✅ Implementado:
  - Concentração excessiva (no console/markdown)

❌ Faltando (notificações automáticas):
  1. Score de ativo caiu > 10% desde última análise
  2. FII com DY abaixo de Selic (oportunidade)
  3. Ação entrou em sobrecompra (P/L > 2σ)
  4. Renda fixa com spread muito alto
  5. Carteira desbalanceada (RV/RF saiu de range)
  6. Novo ativo com score < 3 foi adicionado
  7. Top ativo mudou de posição (concentração aumentando)
```

**Implementação:**
- Comparar scores com última análise (em banco de dados)
- Disparar Telegram/email ao atingir limiares
- Dashboard com histórico de alertas

---

#### 4.3 Histórico de Scores (Time Series)
**Status:** ❌ Não implementado
**Tempo:** 4-5 horas
**Impacto:** ⭐⭐⭐

**Funcionalidade:**
```
Banco de dados (SQLite):
- data (timestamp)
- ticker
- classe
- score
- recomendacao
- macrodados (Selic, IPCA, CDI naquela data)

Dashboard:
- Gráfico de linha: evolução de score por ativo
- Gráfico de boxplot: distribuição de scores ao longo do tempo
- Filtro: período (últimas 2 semanas, 1 mês, 3 meses, etc)
- Tabela: correlação entre mudanças de score e macro

Análise:
- "Score de DEVA11 caiu 2 pontos em 2 semanas"
- "Quando Selic sobe, FIIs perdem 0.8 de score em média"
```

**Implementação:**
- SQLite em data/historico.db
- Inserir nova linha a cada `relatorio.py`
- Nova aba no dashboard: "📈 Histórico"

---

### 🔵 Prioridade 5 — Melhorias de UX/Dados

#### 5.1 Rating de Crédito (S&P/Moody's)
**Status:** ⏳ Framework pronto (tools/calculadores.py)
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

**Implementação:**
- Scraper de S&P, Moody's, Fitch (public data)
- Fallback: base de ratings conhecidos (histórico)
- Integrar ao score de renda fixa

**Teste:** CDB de grande banco, debênture, CRI

---

#### 5.2 Vacância Detalhada (FIIs de Tijolo)
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐⭐

**Implementação:**
- Diferenciar FII de tijolo vs papel automaticamente
- Buscar relatórios gerenciais mensais
- Extrair: vacância física, financeira, por imóvel
- Impacto no score

---

#### 5.3 Rebalanceamento Automático (Recomendação)
**Status:** ❌ Não implementado
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐

**Funcionalidade:**
```
Ao analisar carteira:
1. Identifica desbalanceios (ex: RV 85%, RF 15%)
2. Propõe rebalanceamento:
   - "Venda R$ 5.000 de FII (concentrado)"
   - "Compre R$ 5.000 de Tesouro IPCA+ (diversifique)"
3. Prioriza por:
   - Score baixo (vender primeiro)
   - Liquidez (favorece ativos líquidos)
   - Impostos (minimiza tributação)

Output: Plano de ação passo a passo
```

**Implementação:**
- Algoritmo de otimização de carteira
- Considerar custos de transação

---

#### 5.4 Stress Test (Simulação)
**Status:** ❌ Não implementado
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐

**Funcionalidade:**
```
"Se Selic subir para 15%, qual seria o impacto?"
- Calcular retorno esperado de cada ativo
- Simular para diferentes cenários:
  1. Selic +1% (alta de juros)
  2. Inflação +2% (IPCA sobe)
  3. Câmbio +5% (BRL desvaloriza)
  4. Crise (queda 20% geral)
  5. Recuperação (alta 20% geral)

Output: Exposição de carteira a cada risco
```

**Implementação:**
- Regressão linear: score × macro
- Montecarlo para cenários

---

#### 5.5 Backtesting de Scores
**Status:** ❌ Não implementado
**Tempo:** 4-5 horas
**Impacto:** ⭐⭐

**Funcionalidade:**
```
"Quão bom era meu scoring 3 meses atrás?"
- Comparar scores históricos vs retorno real
- Calcular hit rate: % de recomendações que acertaram
- Ajustar pesos do modelo se necessário

Métrica: Sharpe de uma carteira "buy high score, sell low score"
```

**Implementação:**
- Backtest framework com histórico
- Análise de sensibilidade

---

#### 5.6 Exportação de Relatório em Múltiplos Formatos
**Status:** ⏳ Markdown implementado
**Tempo:** 2-3 horas
**Impacto:** ⭐⭐

**Formatos:**
- ✅ Markdown
- ❌ PDF (com layout bonito)
- ❌ Excel (com gráficos)
- ❌ HTML interativo

---

#### 5.7 API REST
**Status:** ❌ Não implementado
**Tempo:** 5-6 horas
**Impacto:** ⭐⭐⭐

**Endpoints:**
```
GET /api/carteira              → JSON com análise atual
GET /api/carteira/scores       → Scores de todos os ativos
GET /api/carteira/alertas      → Alertas estratégicos
GET /api/macro                 → Dados macroeconômicos
POST /api/analise              → Envia arquivo, retorna análise
GET /api/historico/{ticker}    → Time series de scores
GET /api/simulacao/{cenario}   → Stress test
```

**Implementação:** FastAPI ou Flask

---

### 🟣 Prioridade 6 — Derivativos e Estruturas (Opcional)

#### 6.1 Suporte a Opções
**Status:** ❌ Não implementado
**Tempo:** 5-6 horas
**Impacto:** ⭐

**Implementação:**
- Parser de estratégias (call spread, put protection, etc)
- Cálculo de payoff e risco
- Análise: vale a pena a estrutura?

---

#### 6.2 Suporte a Futuros
**Status:** ❌ Não implementado
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐

---

---

## 📊 Resumo por Tempo Total

| Categoria | Tempo | Impacto |
|---|---|---|
| **Busca Proativa Detalhada (5.1-5.5)** | 12-16h | ⭐⭐⭐⭐⭐ |
| **Ativos Internacionais (2.1-2.4)** | 8-11h | ⭐⭐⭐⭐ |
| **Indicadores Macro (3.1-3.5)** | 6-7h | ⭐⭐⭐ |
| **Automação (4.1-4.3)** | 10-12h | ⭐⭐⭐⭐ |
| **Melhorias UX (5.1-5.7)** | 19-25h | ⭐⭐⭐ |
| **Derivativos (6.1-6.2)** | 8-10h | ⭐ |
| **TOTAL** | **63-81 horas** | — |

---

## 🎯 Roadmap Recomendado

### Fase 1 (Em andamento) — Completar CLAUDE.md
1. ✅ Análise Consolidada (FEITO - 30/05)
2. ✅ Busca Proativa Detalhada — FII (FEITO - 30/05, 3.5h)
3. ⏳ **[PRÓXIMO]** Dashboard FII Detalhes (2-3h) — Aba 9
4. ⏳ Busca Proativa Detalhada — Ações (3-4h)
5. ⏳ Busca Proativa Detalhada — Renda Fixa (2-3h)

**Tempo restante:** 7-10 horas | **Impacto:** Máximo
**Progresso:** 50% (FII feito, faltam ações + RF + dashboard)

### Fase 2 (Próximas 2 semanas) — Automação
1. Watcher + notificações (3-4h)
2. Histórico de scores (4-5h)
3. Alertas em tempo real (3-4h)

**Tempo:** 10-13 horas | **Impacto:** Alto

### Fase 3 (Opcional) — Ativos Internacionais
1. Parser estendido (2-3h)
2. Análise de ações gringas (2-3h)
3. Análise de REITs (2-3h)

**Tempo:** 6-9 horas | **Impacto:** Médio-Alto

### Fase 4 (Opcional) — Melhorias Avançadas
1. Rebalanceamento automático (3-4h)
2. Stress test (3-4h)
3. Backtesting (4-5h)
4. API REST (5-6h)

**Tempo:** 15-19 horas | **Impacto:** Médio

---

## 📝 Notas

- **CLAUDE.md vs Implementação:** O sistema atual cobre ~40% do guia. Faltam dados proativos detalhados.
- **MVP vs Produção:** Fase 1 + 2 = MVP completo (~20h). Fases 3-4 = refinamentos.
- **Prioridades do usuário:** Avaliar com feedback real do uso do dashboard.
- **API externas:** Algumas pendências dependem de acesso a APIs pagas (Bloomberg, Morningstar).

---

## 🔗 Referências

- CLAUDE.md — Guia completo do projeto
- tools/consolidacao.py — Implementação de alertas
- dashboard.py — Interface atual (8 abas)
- relatorio.py — CLI com análise completa

---

**Último update:** 30/05/2026
**Desenvolvedor:** Claude Haiku 4.5
