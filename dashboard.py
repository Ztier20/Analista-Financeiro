#!/usr/bin/env python3
"""
Dashboard Streamlit — Analista Financeiro
Visualiza a análise de carteira com gráficos interativos
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import tempfile
from pathlib import Path
from tools.parser_b3 import ler_extrato_b3
from tools.asset_research import analisar_ativo

# Config página
st.set_page_config(
    page_title="Analista Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Analista Financeiro — Carteira B3")
st.markdown("Análise interativa de ativos em tempo real")

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


def processar_extrato(arquivo):
    """Processa extrato e retorna carteira estruturada + análises"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Salvar arquivo temporário
        temp_path = Path(tmpdir) / arquivo.name
        with open(temp_path, "wb") as f:
            f.write(arquivo.getbuffer())

        # Parsear
        with st.spinner("📖 Lendo extrato..."):
            carteira = ler_extrato_b3(str(temp_path))

        # Analisar cada ativo
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
                    with st.spinner(f"🔍 Analisando {ticker}... ({contador}/{total_ativos})"):
                        resultado = analisar_ativo(ticker, classe)
                        analises[classe].append(resultado)
                except Exception as e:
                    st.warning(f"⚠️  Erro ao analisar {ticker}: {str(e)[:50]}")
                    analises[classe].append({
                        "ticker": ticker,
                        "classe": classe,
                        "erro": str(e)
                    })

                progress_bar.progress(contador / total_ativos)

        return carteira, analises


def criar_grafico_composicao(carteira):
    """Pizza e barra de composição da carteira"""
    col1, col2 = st.columns(2)

    # Pizza: % por classe
    with col1:
        classes_count = {k: len(v) for k, v in carteira.items()}
        fig_pie = px.pie(
            values=list(classes_count.values()),
            names=list(classes_count.keys()),
            title="Composição por Classe",
            hole=0.3
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Barra: valor R$ por ativo
    with col2:
        ativos_data = []
        for classe, ativos in carteira.items():
            for ativo in ativos:
                ativos_data.append({
                    "ticker": ativo["ticker"],
                    "valor": ativo.get("valor_total") or 0,
                    "classe": classe
                })

        df_ativos = pd.DataFrame(ativos_data).sort_values("valor", ascending=True).tail(15)
        fig_bar = px.barh(
            df_ativos,
            x="valor",
            y="ticker",
            color="classe",
            title="Top 15 Ativos por Valor",
            labels={"valor": "Valor (R$)"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def criar_grafico_dividend_yield(analises):
    """Ranking de dividend yield"""
    st.subheader("💰 Dividend Yield")

    dy_data = []

    # FIIs
    for ativo in analises.get("FII", []):
        if "erro" not in ativo:
            dy = ativo.get("dados", {}).get("dividend_yield_12m")
            if dy is not None:
                dy_data.append({
                    "ticker": ativo["ticker"],
                    "dy": dy,
                    "classe": "FII"
                })

    # Ações
    for ativo in analises.get("ACAO_BR", []):
        if "erro" not in ativo:
            dy = ativo.get("dados", {}).get("dividend_yield")
            if dy is not None:
                dy_data.append({
                    "ticker": ativo["ticker"],
                    "dy": dy * 100 if dy < 1 else dy,
                    "classe": "ACAO_BR"
                })

    if dy_data:
        df_dy = pd.DataFrame(dy_data).sort_values("dy", ascending=True)
        fig_dy = px.barh(
            df_dy,
            x="dy",
            y="ticker",
            color="classe",
            title="Ranking de Dividend Yield (%)",
            labels={"dy": "DY (%)"}
        )
        st.plotly_chart(fig_dy, use_container_width=True)
    else:
        st.info("Nenhum dado de dividend yield disponível")


def criar_tabela_valuation(analises):
    """Tabela de valuation das ações"""
    st.subheader("📈 Valuation das Ações")

    acoes_data = []
    for ativo in analises.get("ACAO_BR", []):
        if "erro" not in ativo:
            dados = ativo.get("dados", {})
            acoes_data.append({
                "Ticker": ativo["ticker"],
                "Cotação": f"R$ {dados.get('cotacao_atual', 'N/A')}",
                "Setor": dados.get("setor", "N/A"),
                "P/L": f"{dados.get('p_l', 'N/A'):.2f}" if dados.get('p_l') else "N/A",
                "P/VP": f"{dados.get('p_vp', 'N/A'):.2f}" if dados.get('p_vp') else "N/A",
                "DY (%)": f"{(dados.get('dividend_yield', 0) * 100):.2f}" if dados.get('dividend_yield') else "N/A",
                "Beta": f"{dados.get('beta', 'N/A'):.2f}" if dados.get('beta') else "N/A"
            })

    if acoes_data:
        df_acoes = pd.DataFrame(acoes_data)
        st.dataframe(df_acoes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma ação brasileira na carteira")


def criar_cards_resumo(carteira, analises):
    """Cards de resumo financeiro"""
    st.subheader("📊 Resumo Executivo")

    col1, col2, col3, col4 = st.columns(4)

    # Valor total
    valor_total = sum(
        ativo.get("valor_total", 0) or 0
        for ativos in carteira.values()
        for ativo in ativos
    )
    with col1:
        st.metric("Valor Total", f"R$ {valor_total:,.2f}")

    # Nº de ativos
    total_ativos = sum(len(v) for v in carteira.values())
    with col2:
        st.metric("Nº de Ativos", total_ativos)

    # Maior DY
    maior_dy = 0
    maior_dy_ticker = "N/A"
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            if "erro" not in ativo:
                if classe == "FII":
                    dy = ativo.get("dados", {}).get("dividend_yield_12m", 0) or 0
                elif classe == "ACAO_BR":
                    dy = (ativo.get("dados", {}).get("dividend_yield", 0) or 0) * 100
                else:
                    dy = 0

                if dy > maior_dy:
                    maior_dy = dy
                    maior_dy_ticker = ativo["ticker"]

    with col3:
        st.metric("Maior DY", f"{maior_dy:.2f}% ({maior_dy_ticker})")

    # Ação mais barata (P/L)
    acao_barata = "N/A"
    menor_pl = float('inf')
    for ativo in analises.get("ACAO_BR", []):
        if "erro" not in ativo:
            pl = ativo.get("dados", {}).get("p_l")
            if pl and pl < menor_pl:
                menor_pl = pl
                acao_barata = ativo["ticker"]

    with col4:
        st.metric("Ação mais Barata", f"{acao_barata} (P/L {menor_pl:.1f})" if menor_pl != float('inf') else "N/A")


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Upload")
        arquivo = st.file_uploader(
            "Selecione seu extrato B3 (Excel)",
            type=["xlsx", "xls"],
            help="Arquivo com múltiplas abas (Ações, FII, ETF, Renda Fixa, Tesouro)"
        )

    if arquivo:
        # Processar
        carteira, analises = processar_extrato(arquivo)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Composição", "💰 Dividend Yield", "📈 Valuation", "🎯 Resumo"]
        )

        with tab1:
            criar_grafico_composicao(carteira)

        with tab2:
            criar_grafico_dividend_yield(analises)

        with tab3:
            criar_tabela_valuation(analises)

        with tab4:
            criar_cards_resumo(carteira, analises)

        # Rodapé
        st.divider()
        st.caption("Dados em tempo real via yfinance | Última atualização: " +
                   pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"))

    else:
        st.info(
            "👈 Faça upload do seu extrato B3 na barra lateral para começar a análise!"
        )
        st.markdown("""
        ---
        ### Como usar:
        1. Exporte seu extrato da B3 em Excel
        2. Faça upload usando o botão na barra lateral
        3. Aguarde a análise (alguns segundos)
        4. Visualize os gráficos e dados

        ### Funcionalidades:
        - 📊 Composição da carteira (gráficos de pizza e barra)
        - 💰 Ranking de dividend yield
        - 📈 Análise de valuation das ações (P/L, P/VP)
        - 🎯 Resumo executivo com principais métricas
        """)


if __name__ == "__main__":
    main()
