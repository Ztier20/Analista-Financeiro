# 📋 Pendências — Analista Financeiro

**Status:** v4.0 (11 abas + busca proativa FII/Ações/RF implementadas)
**Data:** 30/05/2026
**Total de Pendências:** 12 itens (40-50 horas de desenvolvimento)

---

## ✅ Implementado (v4.0 — 30/05/2026)

### Dashboard — 11 Abas
- ✅ Aba 1 — Macro (Selic, IPCA, CDI, taxa real)
- ✅ Aba 2 — Scores (cards visuais 0-10)
- ✅ Aba 3 — Ranking (ordenado por score)
- ✅ Aba 4 — Filtros (por faixa de score)
- ✅ Aba 5 — Gráficos (distribuição de scores)
- ✅ Aba 6 — Correlação (matriz + diversificação)
- ✅ Aba 7 — Risco (Sharpe, Sortino, scatter)
- ✅ Aba 8 — Consolidada (concentração, alertas estratégicos)
- ✅ Aba 9 — FII Detalhes (CRIs, vacância, FFO, patrimônio, liquidez)
- ✅ Aba 10 — Ações Detalhes (DRE trimestral, FCF, DL/EBITDA, payout)
- ✅ Aba 11 — Renda Fixa (duration, spread, curva DI, rating emissor)

### Ferramentas (tools/)
- ✅ parser_b3.py — Parser extrato B3 (8+ tipos de ativos)
- ✅ macro_data.py — Selic, IPCA, CDI, câmbio via BCB
- ✅ asset_research.py — Pesquisa proativa por classe
- ✅ scorer.py — Score 0-10 por classe
- ✅ correlacao.py — Matriz de correlação + diversificação
- ✅ risco.py — Sharpe, Sortino
- ✅ consolidacao.py — Concentração, alertas estratégicos
- ✅ fii_analytics.py — Vacância, CRIs, FFO, patrimônio, liquidez (30+ FIIs)
- ✅ acoes_analytics.py — DRE, FCF, DL/EBITDA, payout (8 ações)
- ✅ renda_fixa_analytics.py — Duration, spread, curva, rating emissor

### Entradas/Saídas
- ✅ Dashboard Streamlit (upload extrato B3 .xlsx)
- ✅ CLI: relatorio.py (análise + markdown)
- ✅ Cache por hash de arquivo (invalidação automática)

---

## ⏳ Pendências por Prioridade

### 🔴 Fase 2 — Automação (PRÓXIMA — ~10-13h)

#### 2.1 Histórico de Scores (SQLite)
**Status:** ❌ Não implementado
**Tempo:** 4-5 horas
**Impacto:** ⭐⭐⭐⭐

```
Banco de dados SQLite (data/historico.db):
- Tabela: scores (data, ticker, classe, score, recomendacao, selic, ipca, cdi)
- Inserir nova linha a cada relatorio.py ou upload no dashboard
- Nova aba no dashboard: "📈 Histórico"
  - Gráfico de linha: evolução de score por ativo
  - Filtro: período (últimas 2 semanas, 1 mês, 3 meses)
  - "Score de DEVA11 caiu 2 pontos em 2 semanas"
```

#### 2.2 Alertas em Tempo Real
**Status:** ⏳ Parcialmente (consolidação só no console)
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐⭐

```
Tipos de alertas (faltam):
  ❌ Score caiu > 10% desde última análise
  ❌ FII com DY abaixo de Selic
  ❌ Ação em sobrecompra (P/L > 2σ)
  ❌ Carteira desbalanceada (RV/RF saiu de range)
  ❌ Novo ativo com score < 3

Implementação:
- Comparar scores com última análise (SQLite)
- Exibir alertas no dashboard (aba Consolidada ou nova aba)
```

#### 2.3 Watcher — Monitoramento Automático
**Status:** ❌ Não implementado
**Tempo:** 3-4 horas
**Impacto:** ⭐⭐⭐

```
- Monitorar pasta (ex: ~/Downloads) por novos extratos .xlsx
- Ao detectar: rodar relatorio.py automaticamente
- Salvar em data/relatorios/YYYYMMDD_HHMM/
- Notificação (popup Windows ou log)
Libs: watchdog, APScheduler
```

---

### 🟠 Fase 3 — Ativos Internacionais (~8-11h)

#### 3.1 Parser B3 Estendido para Internacionais
**Status:** ❌ Não implementado
**Tempo:** 2-3 horas

```
Novos tipos:
- ACAO_INTERNACIONAL (AAPL, MSFT)
- REIT_INTERNACIONAL (O, AMT)
- ETF_INTERNACIONAL (SPY, QQQ)
- RENDA_FIXA_INTERNACIONAL (TLT, BND)
```

#### 3.2 Análise de Ações Internacionais
**Status:** ❌ Não implementado — Tempo: 2-3h
- Valuation em USD (P/L, P/VP, EV/EBITDA)
- Impacto cambial em reais
- Fed Funds Rate como contexto

#### 3.3 Análise de REITs Internacionais
**Status:** ❌ Não implementado — Tempo: 2-3h
- FFO por cota, DY, taxa de ocupação, P/FFO

#### 3.4 Análise de Bonds Internacionais
**Status:** ❌ Não implementado — Tempo: 2h
- Duration, YTM, grau de investimento, curva americana

---

### 🟡 Fase 4 — Indicadores Macro Adicionais (~4-5h)

#### 4.1 PIB Brasileiro
**Status:** ❌ — Tempo: 0.5h — BCB Open Data

#### 4.2 Fed Funds Rate
**Status:** ❌ — Tempo: 0.5h — FRED API

#### 4.3 DXY (Dólar Index)
**Status:** ❌ — Tempo: 0.5h — yfinance

#### 4.4 Curva de Juros DI Futuro (tempo real)
**Status:** ⏳ Parcial (referência estática no renda_fixa_analytics.py)
**Tempo:** 2h — B3 API ou Anbima

#### 4.5 Spreads de Crédito
**Status:** ❌ — Tempo: 1-2h — Anbima API

---

### 🟢 Fase 5 — Melhorias Avançadas (~15-20h)

#### 5.1 Rebalanceamento Automático
**Status:** ❌ — Tempo: 3-4h
- Propor vendas/compras para rebalancear carteira
- Considerar liquidez e impostos

#### 5.2 Stress Test (Simulação de Cenários)
**Status:** ❌ — Tempo: 3-4h
- "Se Selic subir para 16%, qual o impacto?"
- Cenários: alta juros, inflação, câmbio, crise, recuperação

#### 5.3 Backtesting de Scores
**Status:** ❌ — Tempo: 4-5h
- Comparar scores históricos vs retorno real
- Hit rate de recomendações

#### 5.4 Exportação PDF/Excel
**Status:** ⏳ Markdown implementado — Tempo: 2-3h
- PDF com layout bonito
- Excel com gráficos

#### 5.5 API REST (FastAPI)
**Status:** ❌ — Tempo: 5-6h
- GET /api/carteira, /api/scores, /api/alertas, /api/macro
- POST /api/analise (upload extrato → análise)

#### 5.6 Suporte a Opções e Futuros
**Status:** ❌ — Tempo: 8-10h — Opcional

---

## 📊 Resumo por Fase

| Fase | Itens | Tempo | Prioridade |
|------|-------|-------|------------|
| **2 — Automação** | 3 itens | 10-13h | 🔴 Alta |
| **3 — Internacionais** | 4 itens | 8-11h | 🟠 Média-Alta |
| **4 — Macro Adicional** | 5 itens | 4-5h | 🟡 Média |
| **5 — Avançado** | 6 itens | 17-22h | 🟢 Baixa |
| **TOTAL** | 18 itens | ~40-51h | — |

---

**Último update:** 30/05/2026 — v4.0
