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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            ["📈 Macro", "🎯 Scores", "📊 Ranking", "🔍 Filtros", "📉 Gráficos", "🔗 Correlação", "⚡ Risco", "🎯 Consolidada"]
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
