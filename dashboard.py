#!/usr/bin/env python3
"""
Dashboard Analista Financeiro Especialista com Scores
Visualiza análises, recomendações, scores e contexto macroeconômico
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tempfile
from pathlib import Path
from datetime import datetime

from tools.parser_b3 import ler_extrato_b3
from tools.macro_data import macro
from tools.asset_research import analisar_ativo
from tools.scorer import calcular_score_por_classe
from tools.correlacao import calcular_correlacao, interpretar_correlacao
from tools.risco import calcular_risco_carteira
from tools.consolidacao import analisar_concentracao, gerar_alertas_estrategicos
from tools.fii_analytics import analisar_fii_completo
from tools.acoes_analytics import analisar_acao_completa
from tools.renda_fixa_analytics import analisar_rf_completo, CURVA_DI_REFERENCIA


# Config página
st.set_page_config(
    page_title="Analista Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Analista Financeiro Especialista")
st.markdown("Análise acionável com scores de qualidade dos ativos")


def processar_carteira(arquivo):
    """Processa extrato e gera análise completa com scores"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / arquivo.name
        with open(temp_path, "wb") as f:
            f.write(arquivo.getbuffer())

        # 1. Parsear
        with st.spinner("📖 Lendo extrato..."):
            carteira = ler_extrato_b3(str(temp_path))

        # 2. Macro dados
        with st.spinner("📈 Obtendo contexto macroeconômico..."):
            macro_dados = macro.obter_todas()

        # 3. Analisar ativos
        total_ativos = sum(len(v) for v in carteira.values())
        analises = {}
        contador = 0
        progress_bar = st.progress(0)

        for classe, ativos in carteira.items():
            analises[classe] = []
            for ativo in ativos:
                contador += 1
                ticker = ativo["ticker"]

                try:
                    resultado = analisar_ativo(ticker, classe)

                    # Calcular score
                    score_info = calcular_score_por_classe(
                        classe,
                        ticker,
                        resultado.get("dados", {}) if resultado else {},
                        macro_dados,
                        ativo.get("valor_total", 0)
                    )

                    analises[classe].append({
                        "ticker": ticker,
                        "classe": classe,
                        "dados_yf": resultado.get("dados") if resultado else {},
                        "score": score_info,
                        "valor": ativo.get("valor_total", 0)
                    })
                except Exception as e:
                    analises[classe].append({
                        "ticker": ticker,
                        "classe": classe,
                        "erro": str(e),
                        "score": {"score": "N/A", "categoria": "Erro"},
                        "valor": ativo.get("valor_total", 0)
                    })

                progress_bar.progress(contador / total_ativos)

        # Invalidar caches para novo upload
        if "correlacao_resultado" in st.session_state:
            del st.session_state["correlacao_resultado"]
        if "risco_resultado" in st.session_state:
            del st.session_state["risco_resultado"]
        if "consolidacao_resultado" in st.session_state:
            del st.session_state["consolidacao_resultado"]

        return carteira, analises, macro_dados


def exibir_contexto_macro(macro_dados):
    """Exibe contexto macroeconômico em cards"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Selic", f"{macro_dados.get('selic', 0):.2f}%", "a.a.")
    with col2:
        st.metric("IPCA 12m", f"{macro_dados.get('ipca_12m', 0):.2f}%", "a.a.")
    with col3:
        st.metric("CDI", f"{macro_dados.get('cdi', 0):.2f}%", "a.a.")
    with col4:
        taxa_real = macro_dados.get('selic', 0) - macro_dados.get('ipca_12m', 0)
        st.metric("Taxa Real", f"{taxa_real:.2f}%", "Selic - IPCA")


def exibir_scores_cards(analises):
    """Exibe cards com scores dos ativos"""
    st.subheader("🎯 Scores de Qualidade dos Ativos")

    # Coletar todos os ativos com scores
    ativos_com_score = []
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score = ativo.get("score", {}).get("score", "N/A")
            if isinstance(score, (int, float)):
                ativos_com_score.append({
                    "ticker": ativo["ticker"],
                    "classe": classe,
                    "score": score,
                    "categoria": ativo.get("score", {}).get("categoria", "N/A"),
                    "valor": ativo.get("valor", 0)
                })

    if not ativos_com_score:
        st.warning("Nenhum score disponível")
        return

    # Ordenar por score decrescente
    ativos_com_score.sort(key=lambda x: x["score"] if isinstance(x["score"], (int, float)) else 0, reverse=True)

    # Exibir em colunas
    cols = st.columns(5)
    for idx, ativo in enumerate(ativos_com_score[:20]):  # Top 20
        col = cols[idx % 5]

        score = ativo["score"]
        categoria = ativo["categoria"]

        # Cor por categoria
        cor_bg = {
            "Excelente": "🟢",
            "Muito Atrativo": "🟢",
            "Bom": "🟡",
            "Atrativo": "🟡",
            "Neutro": "⚪",
            "Fraco": "🔴",
            "Pouco Atrativo": "🔴",
            "Crítico": "🔴"
        }.get(categoria, "⚪")

        with col:
            st.metric(
                f"{cor_bg} {ativo['ticker']}",
                f"{score:.1f}" if isinstance(score, (int, float)) else "N/A",
                categoria,
                label_visibility="visible"
            )


def exibir_ranking_scores(analises):
    """Exibe ranking de ativos por score"""
    st.subheader("📊 Ranking de Ativos por Score")

    # Coletar dados
    ranking_data = []
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score = ativo.get("score", {}).get("score", "N/A")
            if isinstance(score, (int, float)):
                ranking_data.append({
                    "Ticker": ativo["ticker"],
                    "Classe": classe,
                    "Score": score,
                    "Categoria": ativo.get("score", {}).get("categoria", "N/A"),
                    "Valor (R$)": f"{ativo.get('valor', 0):,.2f}" if ativo.get('valor') else "N/D"
                })

    if ranking_data:
        df_ranking = pd.DataFrame(ranking_data).sort_values("Score", ascending=False)
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado disponível")


def exibir_filtro_scores(analises):
    """Exibe tabela com filtro por faixa de score"""
    st.subheader("🔍 Filtro por Faixa de Score")

    # Selector de faixa
    col1, col2 = st.columns(2)
    with col1:
        score_min = st.slider("Score mínimo", 0, 10, 5)
    with col2:
        score_max = st.slider("Score máximo", 0, 10, 10)

    # Coletar dados filtrados
    ativos_filtrados = []
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score = ativo.get("score", {}).get("score", "N/A")
            if isinstance(score, (int, float)) and score_min <= score <= score_max:
                ativos_filtrados.append({
                    "Ticker": ativo["ticker"],
                    "Classe": classe,
                    "Score": f"{score:.1f}",
                    "Categoria": ativo.get("score", {}).get("categoria", "N/A"),
                    "DY": f"{(ativo.get('dados_yf', {}).get('dividend_yield', 0) * 100):.2f}%" if ativo.get('dados_yf', {}).get('dividend_yield') else "N/A",
                    "P/L": f"{ativo.get('dados_yf', {}).get('p_l', 'N/A'):.1f}" if ativo.get('dados_yf', {}).get('p_l') else "N/A"
                })

    if ativos_filtrados:
        df_filtrado = pd.DataFrame(ativos_filtrados)
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(ativos_filtrados)} ativo(s)")
    else:
        st.warning("Nenhum ativo nessa faixa de score")


def exibir_graficos_scores(analises):
    """Exibe gráficos de distribuição de scores"""
    st.subheader("📈 Distribuição de Scores")

    # Coletar scores
    scores = []
    categorias = []
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score = ativo.get("score", {}).get("score", "N/A")
            if isinstance(score, (int, float)):
                scores.append(score)
                categorias.append(ativo.get("score", {}).get("categoria", "N/A"))

    if not scores:
        st.warning("Nenhum score disponível para gráfico")
        return

    col1, col2 = st.columns(2)

    # Histograma de scores
    with col1:
        fig_hist = px.histogram(
            x=scores,
            nbins=10,
            title="Distribuição de Scores",
            labels={"x": "Score", "count": "Quantidade"},
            color_discrete_sequence=["#1f77b4"]
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Gráfico de categorias
    with col2:
        categoria_count = pd.Series(categorias).value_counts()
        fig_cat = px.pie(
            values=categoria_count.values,
            names=categoria_count.index,
            title="Distribuição por Categoria"
        )
        st.plotly_chart(fig_cat, use_container_width=True)


def exibir_correlacao(carteira):
    """Exibe análise de correlação e diversificação da carteira"""
    st.subheader("🔗 Análise de Correlação")

    # Cache para não recalcular ao trocar aba
    CACHE_KEY = "correlacao_resultado"

    if CACHE_KEY not in st.session_state:
        with st.spinner("Buscando histórico de preços..."):
            resultado = calcular_correlacao(carteira)
            st.session_state[CACHE_KEY] = resultado
    else:
        resultado = st.session_state[CACHE_KEY]

    if resultado is None:
        st.warning(
            "Não foi possível calcular correlação. "
            "São necessários pelo menos 2 ativos com histórico de mercado "
            "(FII, ACAO_BR, BDR ou ETF_BR)."
        )
        return

    # Informações sobre análise
    col1, col2, col3 = st.columns(3)
    col1.metric("Correlação Média Absoluta", f"{resultado['n_ativos']:.0f}",
                "ativos com dados")
    col2.metric("Ativos Analisados", resultado['n_ativos'])
    col3.metric("Dias de Histórico", resultado['n_dias'])

    # Avisos
    if resultado['tickers_falha']:
        st.warning(f"Sem dados históricos: {', '.join(resultado['tickers_falha'][:5])}")

    st.divider()

    # Heatmap de correlação
    st.subheader("Matriz de Correlação — Retornos Diários")

    fig = px.imshow(
        resultado["matriz"],
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlação entre ativos (período: 1 ano)",
        aspect="auto",
        labels={"color": "Correlação"}
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Interpretação
    interpretacao = interpretar_correlacao(resultado["matriz"])
    media_corr = interpretacao.get("media_correlacao_absoluta", 0)

    # Classificação de diversificação
    if media_corr < 0.3:
        emoji_div = "✅"
        status_div = "Bem diversificada"
    elif media_corr < 0.6:
        emoji_div = "🟡"
        status_div = "Diversificação moderada"
    else:
        emoji_div = "⚠️"
        status_div = "Concentrada (correlações altas)"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚠️ Alta Correlação (> 0.85)")
        pares_alta = interpretacao.get("pares_alta_correlacao", [])
        if pares_alta:
            for par in pares_alta[:5]:
                st.write(f"  • {par['Ativo A']} ↔ {par['Ativo B']}: {par['Correlação']:.3f}")
        else:
            st.success("Nenhum par com correlação muito alta")

    with col2:
        st.subheader("✅ Correlação Negativa (< -0.3)")
        pares_neg = interpretacao.get("pares_correlacao_negativa", [])
        if pares_neg:
            for par in pares_neg[:5]:
                st.write(f"  • {par['Ativo A']} ↔ {par['Ativo B']}: {par['Correlação']:.3f}")
        else:
            st.info("Sem pares com correlação negativa (diversificadores)")

    st.divider()

    # Ranking de pares
    st.subheader("📋 Ranking de Correlações por Par")
    n_pares = st.slider("Exibir top N pares", 5, 30, 15)

    df_top = interpretacao.get("top_pares", pd.DataFrame())
    if not df_top.empty:
        st.dataframe(df_top.head(n_pares), use_container_width=True, hide_index=True)
    else:
        st.warning("Sem dados de pares")

    # Resumo de diversificação
    st.divider()
    st.info(
        f"**{emoji_div} Carteira {status_div}**  \n"
        f"Correlação média absoluta: {media_corr:.3f}  \n"
        f"(< 0.3 = bem diversificada | 0.3-0.6 = moderada | > 0.6 = concentrada)"
    )


def exibir_risco(carteira, macro_dados):
    """Exibe análise de risco — Sharpe e Sortino por ativo"""
    st.subheader("⚡ Análise de Risco Ajustado")

    # Cache
    CACHE_KEY = "risco_resultado"

    if CACHE_KEY not in st.session_state:
        with st.spinner("Calculando Sharpe e Sortino..."):
            resultado = calcular_risco_carteira(carteira, macro_dados)
            st.session_state[CACHE_KEY] = resultado
    else:
        resultado = st.session_state[CACHE_KEY]

    if resultado is None:
        st.warning(
            "Não foi possível calcular risco. "
            "São necessários pelo menos 1 ativo com histórico de mercado."
        )
        return

    df_risco = resultado["tabela_risco"]
    cdi = resultado["cdi_usado"]

    # Info
    col1, col2, col3 = st.columns(3)
    col1.metric("CDI (Taxa Livre de Risco)", f"{cdi:.2f}%")
    col2.metric("Ativos Analisados", resultado["n_ativos"])
    col3.metric("Período", "1 ano")

    st.divider()

    # Tabela completa
    st.subheader("📊 Tabela de Risco")
    st.dataframe(df_risco, use_container_width=True, hide_index=True)

    st.divider()

    # Gráficos
    col1, col2 = st.columns(2)

    # Sharpe
    with col1:
        st.subheader("Sharpe por Ativo")
        df_sharpe = df_risco.dropna(subset=["Sharpe"]).sort_values("Sharpe")

        if not df_sharpe.empty:
            fig = px.bar(
                df_sharpe,
                x="Sharpe",
                y="Ticker",
                orientation="h",
                color="Classificacao",
                color_discrete_map={
                    "Excelente": "#2ecc71",
                    "Bom": "#3498db",
                    "Aceitável": "#f39c12",
                    "Ruim": "#e74c3c"
                },
                title="Índice de Sharpe"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de Sharpe")

    # Sortino
    with col2:
        st.subheader("Sortino por Ativo")
        df_sortino = df_risco.dropna(subset=["Sortino"]).sort_values("Sortino")

        if not df_sortino.empty:
            fig = px.bar(
                df_sortino,
                x="Sortino",
                y="Ticker",
                orientation="h",
                color_discrete_sequence=["#9b59b6"],
                title="Índice de Sortino"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de Sortino")

    st.divider()

    # Scatter: Retorno vs Volatilidade
    st.subheader("Retorno × Volatilidade (Risco)")

    df_scatter = df_risco.copy()
    df_scatter["Tamanho"] = df_scatter["Sharpe"].abs() * 50
    df_scatter["Tamanho"] = df_scatter["Tamanho"].fillna(10)

    fig = px.scatter(
        df_scatter,
        x="Volatilidade",
        y="Retorno_1y",
        hover_name="Ticker",
        size="Tamanho",
        color="Classificacao",
        color_discrete_map={
            "Excelente": "#2ecc71",
            "Bom": "#3498db",
            "Aceitável": "#f39c12",
            "Ruim": "#e74c3c",
            "N/A": "#95a5a6"
        },
        title="Eficiência de Risco (maior para a esquerda, melhor para cima)",
        labels={"Volatilidade": "Volatilidade (%)", "Retorno_1y": "Retorno 1 ano (%)"}
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Interpretação
    st.info(
        """
        **Como ler:**
        - **Sharpe**: Retorno excedente por unidade de risco (volatilidade total)
          - > 1.0: Excelente | 0.5-1.0: Bom | 0-0.5: Aceitável | < 0: Ruim

        - **Sortino**: Retorno excedente por unidade de risco negativo (downside)
          - Mais relevante que Sharpe pois penaliza apenas quedas

        - **Scatter**: Ativos no canto superior esquerdo são melhores (alto retorno + baixa volatilidade)

        - **Taxa Livre de Risco**: CDI (14.40%) — retorno sem risco de mercado
        """
    )


def exibir_consolidacao(carteira, analises, macro_dados):
    """Exibe análise consolidada da carteira"""

    # Preparar relatorio_ativos para consolidacao.py
    relatorio_ativos = []
    for classe, analise_list in analises.items():
        for analise in analise_list:
            score_val = analise["score"].get("score", 0) if isinstance(analise["score"], dict) else analise["score"]
            try:
                score_num = float(score_val) if score_val != "N/A" else 0
            except:
                score_num = 0

            relatorio_ativos.append({
                "ticker": analise["ticker"],
                "classe": analise["classe"],
                "valor_total": analise.get("valor", 0),
                "score": score_num,
                "recomendacao": "MANTENHA"
            })

    # Calcular concentração
    concentracao = analisar_concentracao(carteira, relatorio_ativos)

    if not concentracao:
        st.error("❌ Dados insuficientes para análise consolidada")
        return

    # Alertas
    alertas = gerar_alertas_estrategicos(concentracao, relatorio_ativos, macro_dados)

    # Seção 1: Métricas principais
    st.subheader("📊 Visão Geral da Carteira")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Ativos", concentracao["num_ativos"])
    col2.metric("Classes", concentracao["num_classes"])
    col3.metric("Valor Total", f"R$ {concentracao['valor_total_carteira']:,.0f}")
    col4.metric("Herfindahl", f"{concentracao['metricas']['indice_herfindahl']:.0f}")

    st.divider()

    # Seção 2: Concentração por Classe (Pizza)
    st.subheader("💼 Distribuição por Classe")
    conc_classe = concentracao["concentracao_por_classe"]

    if not conc_classe.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig_pizza = px.pie(
                values=conc_classe["valor"],
                names=conc_classe.index,
                title="% da Carteira",
                labels={"value": "Valor (R$)", "index": "Classe"}
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col2:
            st.dataframe(
                conc_classe[["valor", "quantidade", "percentual"]].rename(
                    columns={"valor": "Valor (R$)", "quantidade": "Qty", "percentual": "%"}
                ),
                use_container_width=True
            )

    st.divider()

    # Seção 3: Top 10 Ativos
    st.subheader("🏆 Top 10 Maiores Posições")

    top10 = concentracao["top_10_ativos"].copy()
    top10_display = top10[["ticker", "classe", "valor_total", "percentual", "score"]].copy()
    top10_display.columns = ["Ticker", "Classe", "Valor (R$)", "%", "Score"]
    top10_display["Valor (R$)"] = top10_display["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")
    top10_display["%"] = top10_display["%"].apply(lambda x: f"{x:.1f}%")

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(top10_display, use_container_width=True, hide_index=True)

    with col2:
        fig_top10 = px.bar(
            top10.sort_values("valor_total"),
            x="valor_total",
            y="ticker",
            orientation="h",
            title="Maiores Posições",
            labels={"valor_total": "Valor (R$)", "ticker": ""}
        )
        fig_top10.update_layout(height=400)
        st.plotly_chart(fig_top10, use_container_width=True)

    st.divider()

    # Seção 4: Métricas de Concentração
    st.subheader("📈 Análise de Concentração")
    metricas = concentracao["metricas"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Top 1", f"{metricas['concentracao_top_1']:.1f}%", delta="Recomendado < 15%")
    col2.metric("Top 5", f"{metricas['concentracao_top_5']:.1f}%", delta="Recomendado < 50%")
    col3.metric("Top 10", f"{metricas['concentracao_top_10']:.1f}%")
    col4.metric("Herfindahl", f"{metricas['indice_herfindahl']:.0f}", delta="< 2000 = bem diversificada")

    st.divider()

    # Seção 5: Alertas
    st.subheader("⚠️ Alertas Estratégicos")

    if alertas:
        for alerta in alertas:
            severidade = alerta["severidade"]
            emoji_sev = {"CRÍTICA": "🔴", "ALTA": "🟠", "MÉDIA": "🟡", "BAIXA": "🟢"}.get(severidade, "⚪")

            # Cores para o container
            color_map = {
                "CRÍTICA": "#fee",
                "ALTA": "#fef3cd",
                "MÉDIA": "#fff3cd",
                "BAIXA": "#d4edda"
            }
            color = color_map.get(severidade, "#f0f0f0")

            with st.container(border=True):
                st.markdown(f"### {emoji_sev} {alerta['titulo']} ({severidade})")
                st.markdown(alerta["descricao"])
                st.markdown(f"**→ {alerta['recomendacao']}**")
    else:
        st.success("✅ Carteira bem diversificada! Sem alertas críticos.")

    st.divider()

    # Interpretação
    st.info(
        """
        **Como ler a concentração:**
        - **Top 1 > 30%**: ⚠️ Concentração crítica
        - **Top 5 > 50%**: Carteira pouco diversificada
        - **Herfindahl**: 0 (máxima diversificação) a 10.000 (concentração total)
          - < 2.000: Bem diversificada
          - 2.000-3.000: Razoável
          - > 3.000: Concentrada

        **Recomendação**: Considere rebalancear se houver alertas críticos
        """
    )


def exibir_fii_detalhes(carteira, analises, macro_dados):
    """Aba 9 — Análise detalhada dos FIIs: CRIs, vacância, FFO, patrimônio"""
    st.subheader("📋 FII Detalhes")

    # Extrair FIIs da carteira
    fiis = []
    for classe, ativos_lista in analises.items():
        if classe == "FII":
            for a in ativos_lista:
                fiis.append(a)

    if not fiis:
        st.info("Nenhum FII encontrado na carteira.")
        return

    selic = macro_dados.get("selic", 14.4)

    # Filtros
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        tickers_fii = [a["ticker"] for a in fiis]
        selecionados = st.multiselect(
            "Filtrar FIIs",
            options=tickers_fii,
            default=tickers_fii,
            key="fii_detalhe_filtro"
        )
    with col_f2:
        mostrar_tipo = st.selectbox(
            "Tipo",
            ["Todos", "Papel", "Tijolo"],
            key="fii_detalhe_tipo"
        )

    fiis_filtrados = [a for a in fiis if a["ticker"] in selecionados]

    if not fiis_filtrados:
        st.warning("Nenhum FII selecionado.")
        return

    # Buscar dados detalhados (com cache na session_state)
    if "fii_detalhes_cache" not in st.session_state:
        st.session_state["fii_detalhes_cache"] = {}

    dados_completos = []
    progress = st.progress(0)
    for i, ativo in enumerate(fiis_filtrados):
        ticker = ativo["ticker"]
        dy = ativo.get("dados_yf", {}).get("dividend_yield", 0)
        if dy:
            dy = dy * 100

        if ticker not in st.session_state["fii_detalhes_cache"]:
            resultado = analisar_fii_completo(ticker, dy_anual=dy, selic=selic)
            st.session_state["fii_detalhes_cache"][ticker] = resultado
        else:
            resultado = st.session_state["fii_detalhes_cache"][ticker]

        dados_completos.append({
            "ticker": ticker,
            "score": ativo.get("score", {}).get("score", "N/A"),
            "valor": ativo.get("valor", 0),
            "dy": dy,
            "resultado": resultado
        })
        progress.progress((i + 1) / len(fiis_filtrados))

    # Filtro por tipo
    if mostrar_tipo != "Todos":
        tipo_map = {"Papel": "papel", "Tijolo": "tijolo"}
        dados_completos = [
            d for d in dados_completos
            if d["resultado"]["dados"].get("tipo") == tipo_map[mostrar_tipo]
        ]

    st.divider()

    # ── Seção 1: Tabela resumo ─────────────────────────────────────────────
    st.subheader("📊 Resumo Comparativo")

    rows = []
    for d in dados_completos:
        dados = d["resultado"]["dados"]
        liq = dados.get("liquidez", {})
        pat = dados.get("patrimonio", {})
        fcf = dados.get("fluxo_caixa", {})
        vac = dados.get("vacancia", {})
        port = dados.get("portfolio_cri", {})

        rows.append({
            "Ticker": d["ticker"],
            "Tipo": dados.get("tipo", "N/A").capitalize(),
            "Score": f"{d['score']:.1f}" if isinstance(d["score"], (int, float)) else "N/A",
            "DY Anual": f"{d['dy']:.1f}%" if d["dy"] else "N/A",
            "Liquidez (0-10)": liq.get("liquidity_score", "N/A"),
            "Vol. Médio/dia": f"R$ {liq['valor_volume_medio']:,.0f}" if liq.get("valor_volume_medio") else "N/A",
            "Patrimônio Atual": f"R$ {pat['patrimonio_atual']:,.0f}" if pat.get("patrimonio_atual") else "N/A",
            "Cresc. 12m": f"{pat['crescimento_percentual']:+.1f}%" if pat.get("crescimento_percentual") is not None else "N/A",
            "FFO/cota": f"R$ {fcf['ffo_por_cota_anual']:.2f}" if fcf.get("ffo_por_cota_anual") else "N/A",
            "Payout": f"{fcf['payout_ratio']:.0f}%" if fcf.get("payout_ratio") else "N/A",
            "Sustentab.": fcf.get("sustentabilidade", "N/A"),
            "Ocupação": f"{vac['ocupacao_estimada']*100:.0f}%" if vac.get("ocupacao_estimada") else "—",
            "Nº CRIs": port.get("num_cris", "—"),
            "Duration CRI": f"{port['duration_media_anos']:.1f}a" if port.get("duration_media_anos") else "—",
        })

    df_resumo = pd.DataFrame(rows)
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    st.divider()

    # ── Seção 2: Gráficos comparativos ───────────────────────────────────
    col1, col2 = st.columns(2)

    # Liquidez vs DY
    with col1:
        st.subheader("Liquidez × DY")
        df_plot = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Liquidez": d["resultado"]["dados"].get("liquidez", {}).get("liquidity_score", 0),
                "DY (%)": d["dy"] or 0,
                "Tipo": d["resultado"]["dados"].get("tipo", "N/A")
            }
            for d in dados_completos
        ])
        if not df_plot.empty:
            fig = px.scatter(
                df_plot, x="Liquidez", y="DY (%)",
                text="Ticker", color="Tipo",
                title="Liquidez (0-10) × DY Anual",
                size_max=20
            )
            fig.update_traces(textposition="top center")
            fig.add_hline(y=selic, line_dash="dash", line_color="red",
                          annotation_text=f"Selic {selic:.1f}%")
            st.plotly_chart(fig, use_container_width=True)

    # Payout ratio
    with col2:
        st.subheader("Payout Ratio (FFO utilizado)")
        df_payout = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Payout (%)": d["resultado"]["dados"].get("fluxo_caixa", {}).get("payout_ratio", 0),
                "Sustentab.": d["resultado"]["dados"].get("fluxo_caixa", {}).get("sustentabilidade", "N/A")
            }
            for d in dados_completos if d["resultado"]["dados"].get("fluxo_caixa")
        ])
        if not df_payout.empty:
            fig = px.bar(
                df_payout.sort_values("Payout (%)"),
                x="Payout (%)", y="Ticker", orientation="h",
                color="Sustentab.",
                color_discrete_map={
                    "EXCELENTE": "#2ecc71",
                    "BOA": "#3498db",
                    "PREOCUPANTE": "#e74c3c"
                },
                title="Payout ratio (< 100% = sustentável)"
            )
            fig.add_vline(x=100, line_dash="dash", line_color="red",
                          annotation_text="100%")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Seção 3: Portfólio de CRIs (FIIs de papel) ───────────────────────
    fiis_papel = [d for d in dados_completos if d["resultado"]["dados"].get("tipo") == "papel"]
    if fiis_papel:
        st.subheader("📄 Portfólio de CRIs — FIIs de Papel")

        for d in fiis_papel:
            port = d["resultado"]["dados"].get("portfolio_cri")
            if not port:
                continue

            with st.expander(f"🏦 {d['ticker']} — {port['num_cris']} CRIs | Duration {port['duration_media_anos']:.1f}a"):
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Nº de CRIs", port["num_cris"])
                col_b.metric("Duration Média", f"{port['duration_media_anos']:.1f} anos")
                risco_cor = {"ALTA": "🔴", "MÉDIA": "🟡", "BAIXA": "🟢"}.get(port["risco_concentracao"], "⚪")
                col_c.metric("Risco Concentração", f"{risco_cor} {port['risco_concentracao']}")

                st.write(f"**Indexadores:** {', '.join(port['indexadores_principais'])}")
                st.write(f"**Concentração Top 5:** {port['concentracao_top5']:.0%}")

                if port.get("cris_maiores"):
                    df_cris = pd.DataFrame(port["cris_maiores"])
                    df_cris.columns = [c.title() for c in df_cris.columns]
                    st.dataframe(df_cris, use_container_width=True, hide_index=True)

        st.divider()

    # ── Seção 4: Vacância — FIIs de Tijolo ───────────────────────────────
    fiis_tijolo = [d for d in dados_completos if d["resultado"]["dados"].get("tipo") == "tijolo"]
    if fiis_tijolo:
        st.subheader("🏢 Vacância — FIIs de Tijolo")

        df_vac = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Ocupação (%)": d["resultado"]["dados"].get("vacancia", {}).get("ocupacao_estimada", 0) * 100,
                "Vacância (%)": d["resultado"]["dados"].get("vacancia", {}).get("vacancia_estimada", 0),
                "Confiança": f"{d['resultado']['dados'].get('vacancia', {}).get('confianca', 0):.0%}"
            }
            for d in fiis_tijolo if d["resultado"]["dados"].get("vacancia")
        ])

        if not df_vac.empty:
            fig = px.bar(
                df_vac.sort_values("Ocupação (%)"),
                x="Ocupação (%)", y="Ticker", orientation="h",
                color="Ocupação (%)",
                color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
                range_color=[60, 100],
                title="Taxa de Ocupação (estimada)"
            )
            fig.add_vline(x=80, line_dash="dash", line_color="orange",
                          annotation_text="80% (mínimo saudável)")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_vac, use_container_width=True, hide_index=True)

        st.divider()

    # ── Seção 5: Análise Textual por FII ─────────────────────────────────
    st.subheader("💬 Análise por FII")
    for d in dados_completos:
        tipo = d["resultado"]["dados"].get("tipo", "N/A")
        emoji_tipo = "📄" if tipo == "papel" else "🏢" if tipo == "tijolo" else "📊"
        score = d["score"]
        score_str = f"{score:.1f}" if isinstance(score, (int, float)) else "N/A"

        with st.expander(f"{emoji_tipo} {d['ticker']} | Score {score_str} | DY {d['dy']:.1f}%" if d["dy"] else f"{emoji_tipo} {d['ticker']} | Score {score_str}"):
            st.markdown(d["resultado"]["analise"])


def exibir_acoes_detalhes(analises, macro_dados):
    """Aba 10 — Análise fundamentalista detalhada das ações brasileiras"""
    st.subheader("📈 Ações Detalhes — Análise Fundamentalista")

    # Extrair ações
    acoes = []
    for classe, ativos_lista in analises.items():
        if classe == "ACAO_BR":
            for a in ativos_lista:
                acoes.append(a)

    if not acoes:
        st.info("Nenhuma ação brasileira encontrada na carteira.")
        return

    # Filtros
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        tickers_acao = [a["ticker"] for a in acoes]
        selecionados = st.multiselect(
            "Filtrar ações",
            options=tickers_acao,
            default=tickers_acao,
            key="acao_detalhe_filtro"
        )

    acoes_filtradas = [a for a in acoes if a["ticker"] in selecionados]
    if not acoes_filtradas:
        st.warning("Nenhuma ação selecionada.")
        return

    # Buscar/cache dados completos
    if "acoes_detalhes_cache" not in st.session_state:
        st.session_state["acoes_detalhes_cache"] = {}

    dados_completos = []
    progress = st.progress(0)
    for i, ativo in enumerate(acoes_filtradas):
        ticker = ativo["ticker"]
        dados_yf = ativo.get("dados_yf", {})

        if ticker not in st.session_state["acoes_detalhes_cache"]:
            resultado = analisar_acao_completa(ticker, dados_yf=dados_yf)
            st.session_state["acoes_detalhes_cache"][ticker] = resultado
        else:
            resultado = st.session_state["acoes_detalhes_cache"][ticker]

        dados_completos.append({
            "ticker": ticker,
            "score": ativo.get("score", {}).get("score", "N/A"),
            "valor": ativo.get("valor", 0),
            "dados_yf": dados_yf,
            "resultado": resultado,
        })
        progress.progress((i + 1) / len(acoes_filtradas))

    st.divider()

    # ── Seção 1: Tabela resumo ─────────────────────────────────────────────
    st.subheader("📊 Resumo Comparativo")

    rows = []
    for d in dados_completos:
        rd = d["resultado"]["dados"]
        dre = rd.get("dre", {})
        alav = rd.get("alavancagem", {})
        fcf = rd.get("fcf", {})
        pay = rd.get("payout", {})
        cresc = rd.get("crescimento", {})
        yf = d["dados_yf"]

        margem_ebitda = (
            (dre["ebitda_12m"] / dre["receita_12m"] * 100)
            if dre.get("ebitda_12m") and dre.get("receita_12m") else None
        )
        margem_liq = (
            (dre["lucro_liquido_12m"] / dre["receita_12m"] * 100)
            if dre.get("lucro_liquido_12m") and dre.get("receita_12m") else None
        )

        rows.append({
            "Ticker": d["ticker"],
            "Nome": rd.get("nome", "—"),
            "Setor": rd.get("setor", yf.get("setor", "—")),
            "Score": f"{d['score']:.1f}" if isinstance(d["score"], (int, float)) else "N/A",
            "P/L": f"{yf.get('p_l', 0):.1f}x" if yf.get("p_l") else "N/A",
            "P/VP": f"{yf.get('p_vp', 0):.1f}x" if yf.get("p_vp") else "N/A",
            "DY": f"{(yf.get('dividend_yield') or 0)*100:.1f}%" if yf.get("dividend_yield") else "N/A",
            "Receita 12m": f"R$ {dre['receita_12m']/1e9:.1f}B" if dre.get("receita_12m") else "N/A",
            "Mg. EBITDA": f"{margem_ebitda:.0f}%" if margem_ebitda else "N/A",
            "Mg. Líquida": f"{margem_liq:.0f}%" if margem_liq else "N/A",
            "DL/EBITDA": f"{alav['indice_dl_ebitda']:.1f}x" if alav.get("indice_dl_ebitda") is not None else "N/A",
            "Alavancagem": alav.get("classificacao_alavancagem", "N/A"),
            "FCF 12m": f"R$ {fcf['fcf_12m']/1e9:.1f}B" if fcf.get("fcf_12m") else "N/A",
            "Payout": f"{pay['payout_ratio']:.0f}%" if pay.get("payout_ratio") else "N/A",
            "Cresc. Lucro": f"{cresc['crescimento_ultimo_trimestre']:+.1f}%" if cresc.get("crescimento_ultimo_trimestre") is not None else "N/A",
            "Tendência": cresc.get("tendencia", "N/A"),
        })

    df_resumo = pd.DataFrame(rows)
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    st.divider()

    # ── Seção 2: Gráficos ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    # DL/EBITDA
    with col1:
        st.subheader("Alavancagem (DL/EBITDA)")
        df_alav = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "DL/EBITDA": d["resultado"]["dados"].get("alavancagem", {}).get("indice_dl_ebitda", 0) or 0,
                "Classificação": d["resultado"]["dados"].get("alavancagem", {}).get("classificacao_alavancagem", "N/A"),
            }
            for d in dados_completos if d["resultado"]["dados"].get("alavancagem")
        ])
        if not df_alav.empty:
            fig = px.bar(
                df_alav.sort_values("DL/EBITDA"),
                x="DL/EBITDA", y="Ticker", orientation="h",
                color="Classificação",
                color_discrete_map={
                    "CAIXA LÍQUIDO": "#27ae60",
                    "BAIXA": "#2ecc71",
                    "SAUDÁVEL": "#3498db",
                    "MODERADA": "#f39c12",
                    "ALTA": "#e74c3c",
                },
                title="Dívida Líquida / EBITDA"
            )
            fig.add_vline(x=2, line_dash="dash", line_color="orange",
                          annotation_text="2x (referência)")
            st.plotly_chart(fig, use_container_width=True)

    # Payout ratio
    with col2:
        st.subheader("Payout Ratio")
        df_pay = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Payout (%)": d["resultado"]["dados"].get("payout", {}).get("payout_ratio", 0) or 0,
                "Classificação": d["resultado"]["dados"].get("payout", {}).get("classificacao", "N/A"),
            }
            for d in dados_completos if d["resultado"]["dados"].get("payout")
        ])
        if not df_pay.empty:
            fig = px.bar(
                df_pay.sort_values("Payout (%)"),
                x="Payout (%)", y="Ticker", orientation="h",
                color="Classificação",
                color_discrete_map={
                    "CONSERVADOR": "#3498db",
                    "EQUILIBRADO": "#2ecc71",
                    "GENEROSO": "#f39c12",
                    "INSUSTENTÁVEL": "#e74c3c",
                },
                title="Payout Ratio (% do lucro distribuído)"
            )
            fig.add_vline(x=100, line_dash="dash", line_color="red",
                          annotation_text="100%")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Seção 3: DRE Trimestral ───────────────────────────────────────────
    st.subheader("📋 DRE Trimestral")

    acao_selecionada = st.selectbox(
        "Selecione a ação",
        options=[d["ticker"] for d in dados_completos],
        key="acao_dre_select"
    )

    acao_data = next((d for d in dados_completos if d["ticker"] == acao_selecionada), None)
    if acao_data:
        dre = acao_data["resultado"]["dados"].get("dre", {})
        trimestrais = dre.get("trimestrais", [])

        if trimestrais:
            df_tri = pd.DataFrame(trimestrais)
            df_tri_display = df_tri.copy()
            for col in ["receita", "ebitda", "lucro"]:
                if col in df_tri_display.columns:
                    df_tri_display[col] = df_tri_display[col].apply(
                        lambda x: f"R$ {x/1e9:.2f}B" if pd.notna(x) and x else "N/A"
                    )
            df_tri_display.columns = [c.title() for c in df_tri_display.columns]
            st.dataframe(df_tri_display, use_container_width=True, hide_index=True)

            # Gráfico de barras agrupadas
            df_plot = df_tri.copy()
            df_plot["receita_bi"] = df_plot["receita"].apply(lambda x: x / 1e9 if x else 0)
            df_plot["ebitda_bi"] = df_plot["ebitda"].apply(lambda x: x / 1e9 if x else None)
            df_plot["lucro_bi"] = df_plot["lucro"].apply(lambda x: x / 1e9 if x else 0)

            fig = go.Figure()
            fig.add_bar(x=df_plot["periodo"], y=df_plot["receita_bi"],
                        name="Receita", marker_color="#3498db")
            if df_plot["ebitda_bi"].notna().any():
                fig.add_bar(x=df_plot["periodo"], y=df_plot["ebitda_bi"],
                            name="EBITDA", marker_color="#2ecc71")
            fig.add_bar(x=df_plot["periodo"], y=df_plot["lucro_bi"],
                        name="Lucro Líquido", marker_color="#e67e22")
            fig.update_layout(
                title=f"DRE Trimestral — {acao_selecionada} (R$ Bilhões)",
                barmode="group", height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Dados trimestrais não disponíveis para {acao_selecionada}.")

    st.divider()

    # ── Seção 4: Análise textual por ação ─────────────────────────────────
    st.subheader("💬 Análise por Ação")
    for d in dados_completos:
        score = d["score"]
        score_str = f"{score:.1f}" if isinstance(score, (int, float)) else "N/A"
        nome = d["resultado"]["dados"].get("nome", d["ticker"])

        with st.expander(f"📈 {d['ticker']} — {nome} | Score {score_str}"):
            st.markdown(d["resultado"]["analise"])


def exibir_renda_fixa_detalhes(carteira, analises, macro_dados):
    """Aba 11 — Análise detalhada de renda fixa: duration, spread, curva, rating"""
    st.subheader("🏦 Renda Fixa Detalhes")

    # Classes de renda fixa suportadas
    CLASSES_RF = {"TESOURO_IPCA", "TESOURO_SELIC", "TESOURO_PREFIXADO",
                  "RF_CDB", "RF_LCI", "RF_LCA", "RF_CRI", "RF_CRA",
                  "RF_DEBENTURE", "RF_FIDC", "RENDA_FIXA_PRIVADA"}

    ativos_rf = []
    for classe, ativos_lista in analises.items():
        if any(rf in classe.upper() for rf in
               ["TESOURO", "RF_", "RENDA_FIXA", "CDB", "LCI", "LCA", "CRI", "CRA", "DEBENTURE", "FIDC"]):
            for a in ativos_lista:
                ativos_rf.append({**a, "classe": classe})

    if not ativos_rf:
        st.info("Nenhum ativo de renda fixa encontrado na carteira.")
        return

    selic = macro_dados.get("selic", 14.4)
    cdi = macro_dados.get("cdi", 14.35)
    ipca = macro_dados.get("ipca_12m", 5.5)

    # Filtro
    tickers_rf = [a["ticker"] for a in ativos_rf]
    selecionados = st.multiselect(
        "Filtrar ativos",
        options=tickers_rf,
        default=tickers_rf,
        key="rf_detalhe_filtro"
    )
    ativos_filtrados = [a for a in ativos_rf if a["ticker"] in selecionados]
    if not ativos_filtrados:
        st.warning("Nenhum ativo selecionado.")
        return

    # Cache e busca
    if "rf_detalhes_cache" not in st.session_state:
        st.session_state["rf_detalhes_cache"] = {}

    dados_completos = []
    progress = st.progress(0)
    for i, ativo in enumerate(ativos_filtrados):
        ticker = ativo["ticker"]
        classe = ativo["classe"]
        cache_key = f"{ticker}_{classe}"

        if cache_key not in st.session_state["rf_detalhes_cache"]:
            resultado = analisar_rf_completo(ticker, classe, macro_dados=macro_dados)
            st.session_state["rf_detalhes_cache"][cache_key] = resultado
        else:
            resultado = st.session_state["rf_detalhes_cache"][cache_key]

        dados_completos.append({
            "ticker": ticker,
            "classe": classe,
            "score": ativo.get("score", {}).get("score", "N/A"),
            "valor": ativo.get("valor", 0),
            "resultado": resultado,
        })
        progress.progress((i + 1) / len(ativos_filtrados))

    st.divider()

    # ── Seção 1: Tabela resumo ─────────────────────────────────────────────
    st.subheader("📊 Resumo Comparativo")

    rows = []
    for d in dados_completos:
        rd = d["resultado"]["dados"]
        classif = rd.get("classificacao", {})
        spread = rd.get("spread", {})
        dur = rd.get("duration", {})
        rating = rd.get("rating", {})
        pos = rd.get("posicao_curva", {})

        rows.append({
            "Ticker": d["ticker"],
            "Tipo": classif.get("tipo", "N/A"),
            "Indexador": classif.get("indexador", "N/A"),
            "Score": f"{d['score']:.1f}" if isinstance(d["score"], (int, float)) else "N/A",
            "Taxa (% a.a.)": f"{rd.get('taxa_contratada', 0):.2f}%" if rd.get("taxa_contratada") else "N/A",
            "Benchmark": f"{rd.get('benchmark_nome','CDI')} {rd.get('benchmark_valor',0):.2f}%",
            "Spread (bps)": f"{spread.get('spread_bps', 0):+.0f}" if spread.get("spread_bps") is not None else "N/A",
            "Spread Classif.": spread.get("classificacao", "N/A"),
            "Duration (anos)": f"{dur.get('duration_anos', 0):.1f}a" if dur.get("duration_anos") else "N/A",
            "Duration Classif.": dur.get("classificacao", "N/A"),
            "Rating": rating.get("rating", "N/A"),
            "FGC": "✅" if classif.get("fgc_coberto") else "❌",
            "Isento IR": "✅" if classif.get("isento_ir") else "❌",
            "Posição Curva": f"{pos.get('emoji','')} {pos.get('avaliacao','N/A')}" if pos else "N/A",
        })

    df_resumo = pd.DataFrame(rows)
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    st.divider()

    # ── Seção 2: Curva de Juros DI Futuro ─────────────────────────────────
    st.subheader("📉 Curva de Juros (DI Futuro) × Ativos")

    pontos_curva = {
        "1m": 1/12, "3m": 3/12, "6m": 6/12,
        "1a": 1, "2a": 2, "3a": 3, "5a": 5, "10a": 10
    }

    fig_curva = go.Figure()

    # Linha da curva DI
    x_curva = list(pontos_curva.values())
    y_curva = [CURVA_DI_REFERENCIA[k] for k in pontos_curva]
    fig_curva.add_trace(go.Scatter(
        x=x_curva, y=y_curva,
        mode="lines+markers",
        name="Curva DI Futuro",
        line=dict(color="#3498db", width=2),
    ))

    # Linha da Selic
    fig_curva.add_hline(y=selic, line_dash="dash", line_color="red",
                        annotation_text=f"Selic {selic:.1f}%")

    # Marcar ativos na curva
    for d in dados_completos:
        rd = d["resultado"]["dados"]
        vcto = rd.get("vencimento_anos")
        taxa = rd.get("taxa_contratada")
        if vcto and taxa:
            indexador = rd.get("classificacao", {}).get("indexador", "CDI")
            # Para IPCA+, plotar como taxa total (IPCA + spread)
            taxa_plot = taxa + ipca if indexador == "IPCA" else taxa
            fig_curva.add_trace(go.Scatter(
                x=[vcto], y=[taxa_plot],
                mode="markers+text",
                name=d["ticker"],
                text=[d["ticker"]],
                textposition="top center",
                marker=dict(size=10),
            ))

    fig_curva.update_layout(
        title="Curva DI Futuro e posicionamento dos ativos",
        xaxis_title="Prazo (anos)",
        yaxis_title="Taxa (% a.a.)",
        height=450,
    )
    st.plotly_chart(fig_curva, use_container_width=True)

    st.divider()

    # ── Seção 3: Spread por ativo ──────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spread sobre Benchmark (bps)")
        df_spread = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Spread (bps)": d["resultado"]["dados"].get("spread", {}).get("spread_bps", 0) or 0,
                "Classificação": d["resultado"]["dados"].get("spread", {}).get("classificacao", "N/A"),
            }
            for d in dados_completos if d["resultado"]["dados"].get("spread")
        ])
        if not df_spread.empty:
            fig = px.bar(
                df_spread.sort_values("Spread (bps)"),
                x="Spread (bps)", y="Ticker", orientation="h",
                color="Classificação",
                color_discrete_map={
                    "MUITO ALTO": "#e74c3c",
                    "ALTO": "#e67e22",
                    "MODERADO": "#f1c40f",
                    "BAIXO": "#2ecc71",
                    "ABAIXO DO BENCHMARK": "#95a5a6",
                },
                title="Spread vs Benchmark"
            )
            fig.add_vline(x=0, line_dash="solid", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Duration por Ativo")
        df_dur = pd.DataFrame([
            {
                "Ticker": d["ticker"],
                "Duration (anos)": d["resultado"]["dados"].get("duration", {}).get("duration_anos", 0) or 0,
                "Classif.": d["resultado"]["dados"].get("duration", {}).get("classificacao", "N/A"),
            }
            for d in dados_completos if d["resultado"]["dados"].get("duration")
        ])
        if not df_dur.empty:
            fig = px.bar(
                df_dur.sort_values("Duration (anos)"),
                x="Duration (anos)", y="Ticker", orientation="h",
                color="Classif.",
                color_discrete_map={
                    "CURTÍSSIMA": "#2ecc71",
                    "CURTA": "#27ae60",
                    "MÉDIA": "#f39c12",
                    "LONGA": "#e67e22",
                    "MUITO LONGA": "#e74c3c",
                },
                title="Duration (sensibilidade a juros)"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Seção 4: Análise textual por ativo ────────────────────────────────
    st.subheader("💬 Análise por Ativo")
    for d in dados_completos:
        classif = d["resultado"]["dados"].get("classificacao", {})
        tipo = classif.get("tipo", "N/A")
        score = d["score"]
        score_str = f"{score:.1f}" if isinstance(score, (int, float)) else "N/A"
        taxa = d["resultado"]["dados"].get("taxa_contratada")
        taxa_str = f" | {taxa:.2f}% a.a." if taxa else ""

        with st.expander(f"🏦 {d['ticker']} — {tipo}{taxa_str} | Score {score_str}"):
            st.markdown(d["resultado"]["analise"])

            # Info extra: FGC + Isento IR
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("FGC", "✅ Coberto" if classif.get("fgc_coberto") else "❌ Não coberto")
            col_b.metric("Imposto IR", "✅ Isento" if classif.get("isento_ir") else "❌ Tributável")
            rating = d["resultado"]["dados"].get("rating", {})
            col_c.metric("Rating Emissor", rating.get("rating", "N/A"))


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Upload")
        arquivo = st.file_uploader(
            "Selecione seu extrato B3 (Excel)",
            type=["xlsx", "xls"]
        )

    if arquivo:
        # Processar
        carteira, analises, macro_dados = processar_carteira(arquivo)

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(
            ["📈 Macro", "🎯 Scores", "📊 Ranking", "🔍 Filtros", "📉 Gráficos", "🔗 Correlação", "⚡ Risco", "🎯 Consolidada", "📋 FII Detalhes", "📈 Ações Detalhes", "🏦 Renda Fixa"]
        )

        with tab1:
            st.subheader("Contexto Macroeconômico Atual")
            exibir_contexto_macro(macro_dados)

            st.divider()
            st.markdown("""
            **Interpretação:**
            - **Selic elevada** → Pressiona FIIs e ações, favorece renda fixa
            - **Taxa Real** (Selic - IPCA) → Retorno real de ativos
            - **CDI** → Benchmark para renda fixa privada
            """)

        with tab2:
            exibir_scores_cards(analises)

        with tab3:
            exibir_ranking_scores(analises)

        with tab4:
            exibir_filtro_scores(analises)

        with tab5:
            exibir_graficos_scores(analises)

        with tab6:
            exibir_correlacao(carteira)

        with tab7:
            exibir_risco(carteira, macro_dados)

        with tab8:
            exibir_consolidacao(carteira, analises, macro_dados)

        with tab9:
            exibir_fii_detalhes(carteira, analises, macro_dados)

        with tab10:
            exibir_acoes_detalhes(analises, macro_dados)

        with tab11:
            exibir_renda_fixa_detalhes(carteira, analises, macro_dados)

        # Rodapé
        st.divider()
        st.caption(
            f"Análise gerada em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} | "
            f"Scores 0-10 por qualidade do ativo"
        )

    else:
        st.info("👈 Faça upload do seu extrato B3 para começar!")

        st.markdown("""
        ---
        ### 🚀 Como usar:

        1. **Exporte seu extrato da B3** em Excel
        2. **Faça upload** na barra lateral
        3. **Veja os scores** de cada ativo (0-10)

        ---

        ### 📊 Abas disponíveis:

        - **Macro** — Selic, IPCA, CDI, taxa real
        - **Scores** — Cards visuais de cada ativo
        - **Ranking** — Ativos ordenados por score
        - **Filtros** — Filtrar por faixa de score
        - **Gráficos** — Distribuição de scores
        - **FII Detalhes** — CRIs, vacância, FFO, patrimônio por FII
        - **Ações Detalhes** — DRE trimestral, FCF, alavancagem, payout por ação
        - **Renda Fixa** — Duration, spread, rating, posição na curva de juros

        ---

        ### 🎯 Sistema de Scores:

        **0-3:** Crítico/Pouco Atrativo 🔴
        **4-5:** Fraco/Neutro ⚪
        **6-7:** Bom/Atrativo 🟡
        **8-10:** Excelente/Muito Atrativo 🟢

        Scores consideram:
        - **Ações:** Valuation (P/L, P/VP), DY, Beta
        - **FIIs:** DY vs Selic, liquidez
        - **Renda Fixa:** Taxa vs CDI, spread
        - **Tesouro:** Taxa real, proteção
        """)


if __name__ == "__main__":
    main()
