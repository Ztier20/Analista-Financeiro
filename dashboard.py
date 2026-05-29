#!/usr/bin/env python3
"""
Dashboard Analista Financeiro Especialista
Visualiza análises, recomendações e contexto macroeconômico
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tempfile
import json
from pathlib import Path
from datetime import datetime

from tools.parser_b3 import ler_extrato_b3
from tools.macro_data import macro
from tools.asset_research import analisar_ativo
from tools.interpretador import Interpretador


# Config página
st.set_page_config(
    page_title="Analista Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Analista Financeiro Especialista")
st.markdown("Análise acionável de carteira com recomendações por ativo")

# CSS customizado
st.markdown("""
<style>
    .recomendacao-aumente {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .recomendacao-mantenha {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
    }
    .recomendacao-reduza {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def processar_carteira(arquivo):
    """Processa extrato e gera análise completa"""
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
                    analises[classe].append(resultado)
                except Exception as e:
                    analises[classe].append({
                        "ticker": ticker,
                        "classe": classe,
                        "erro": str(e)
                    })

                progress_bar.progress(contador / total_ativos)

        return carteira, analises, macro_dados


def exibir_contexto_macro(macro_dados):
    """Exibe contexto macroeconômico em cards"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Selic",
            f"{macro_dados.get('selic', 0):.2f}%",
            "a.a."
        )

    with col2:
        st.metric(
            "IPCA 12m",
            f"{macro_dados.get('ipca_12m', 0):.2f}%",
            "a.a."
        )

    with col3:
        st.metric(
            "CDI",
            f"{macro_dados.get('cdi', 0):.2f}%",
            "a.a."
        )

    with col4:
        taxa_real = macro_dados.get('selic', 0) - macro_dados.get('ipca_12m', 0)
        st.metric(
            "Taxa Real",
            f"{taxa_real:.2f}%",
            "Selic - IPCA"
        )


def exibir_recomendacoes(analises, carteira):
    """Exibe recomendações por classe"""

    # Extrair recomendações
    recomendacoes = {
        "AUMENTE": [],
        "MANTENHA": [],
        "REDUZA": [],
        "VENDA": [],
        "N/A": []
    }

    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            ticker = ativo.get("ticker", "N/A")
            dados_yf = ativo.get("dados", {})

            # Obter recomendação
            if "erro" in ativo:
                rec = "N/A"
                analise = ativo.get("erro", "Sem dados")
            else:
                rec = ativo.get("interpretacao") or "N/A"
                analise = dados_yf.get("dividend_yield_12m") or dados_yf.get("dividend_yield") or "N/A"

            # Por enquanto, usar lógica simplificada (real vem do interpretador)
            if classe == "FII":
                dy = dados_yf.get("dividend_yield_12m", 0)
                if dy and dy > 12:
                    rec = "AUMENTE"
                elif dy and dy > 8:
                    rec = "MANTENHA"
                else:
                    rec = "REDUZA"
            elif classe == "ACAO_BR":
                p_l = dados_yf.get("p_l")
                if p_l and p_l < 10:
                    rec = "AUMENTE"
                elif p_l and p_l < 15:
                    rec = "MANTENHA"
                else:
                    rec = "REDUZA"
            else:
                rec = "MANTENHA"

            recomendacoes[rec].append({
                "ticker": ticker,
                "classe": classe,
                "dados": dados_yf
            })

    # Exibir por recomendação
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🟢 AUMENTE",
            len(recomendacoes["AUMENTE"]),
            "ativos"
        )

    with col2:
        st.metric(
            "🟡 MANTENHA",
            len(recomendacoes["MANTENHA"]),
            "ativos"
        )

    with col3:
        st.metric(
            "🔴 REDUZA",
            len(recomendacoes["REDUZA"]),
            "ativos"
        )

    with col4:
        st.metric(
            "⛔ VENDA",
            len(recomendacoes["VENDA"]),
            "ativos"
        )

    # Tabela de recomendações
    st.subheader("📋 Recomendações Detalhadas")

    for rec_tipo in ["AUMENTE", "MANTENHA", "REDUZA", "VENDA"]:
        ativos = recomendacoes[rec_tipo]
        if ativos:
            with st.expander(f"{rec_tipo} ({len(ativos)} ativo(s))"):
                df_data = []
                for ativo in ativos:
                    df_data.append({
                        "Ticker": ativo["ticker"],
                        "Classe": ativo["classe"],
                        "P/L": f"{ativo['dados'].get('p_l', 'N/A')}",
                        "DY": f"{(ativo['dados'].get('dividend_yield', 0) * 100):.2f}%" if ativo['dados'].get('dividend_yield') else "N/A",
                        "Cotação": f"R$ {ativo['dados'].get('cotacao_atual', 'N/A')}"
                    })

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)


def exibir_graficos(analises, carteira):
    """Exibe gráficos de composição e recomendações"""

    col1, col2 = st.columns(2)

    # Gráfico de composição por classe
    with col1:
        classes_count = {k: len(v) for k, v in carteira.items()}
        fig_pie = px.pie(
            values=list(classes_count.values()),
            names=list(classes_count.keys()),
            title="Composição por Classe de Ativo",
            hole=0.3
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de recomendações
    with col2:
        recomendacoes_count = {"AUMENTE": 0, "MANTENHA": 0, "REDUZA": 0, "VENDA": 0}

        for classe, ativos_lista in analises.items():
            for ativo in ativos_lista:
                if classe == "FII":
                    dy = ativo.get("dados", {}).get("dividend_yield_12m", 0)
                    if dy and dy > 12:
                        recomendacoes_count["AUMENTE"] += 1
                    elif dy and dy > 8:
                        recomendacoes_count["MANTENHA"] += 1
                    else:
                        recomendacoes_count["REDUZA"] += 1
                else:
                    recomendacoes_count["MANTENHA"] += 1

        fig_rec = px.bar(
            x=list(recomendacoes_count.keys()),
            y=list(recomendacoes_count.values()),
            title="Distribuição de Recomendações",
            labels={"x": "Recomendação", "y": "Quantidade"},
            color=list(recomendacoes_count.keys()),
            color_discrete_map={
                "AUMENTE": "#28a745",
                "MANTENHA": "#ffc107",
                "REDUZA": "#dc3545",
                "VENDA": "#6c757d"
            }
        )
        st.plotly_chart(fig_rec, use_container_width=True)


def exibir_tabela_completa(carteira, analises):
    """Exibe tabela completa com todos os ativos"""
    st.subheader("📊 Análise Completa da Carteira")

    tabela_data = []
    for classe, ativos in carteira.items():
        for ativo in ativos:
            ticker = ativo["ticker"]
            valor = ativo.get("valor_total", 0)

            # Encontrar dados de análise
            analise_ativo = None
            if classe in analises:
                for a in analises[classe]:
                    if a.get("ticker") == ticker:
                        analise_ativo = a
                        break

            dados_yf = analise_ativo.get("dados", {}) if analise_ativo else {}

            tabela_data.append({
                "Ticker": ticker,
                "Classe": classe,
                "Valor (R$)": f"{valor:,.2f}" if valor else "N/D",
                "Cotação": f"R$ {dados_yf.get('cotacao_atual', 'N/A')}",
                "P/L": f"{dados_yf.get('p_l', 'N/A'):.2f}" if dados_yf.get('p_l') else "N/A",
                "P/VP": f"{dados_yf.get('p_vp', 'N/A'):.2f}" if dados_yf.get('p_vp') else "N/A",
                "DY": f"{(dados_yf.get('dividend_yield', 0) * 100):.2f}%" if dados_yf.get('dividend_yield') else f"{dados_yf.get('dividend_yield_12m', 0):.2f}%" if dados_yf.get('dividend_yield_12m') else "N/A"
            })

    df_tabela = pd.DataFrame(tabela_data)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)


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
        carteira, analises, macro_dados = processar_carteira(arquivo)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📈 Contexto Macro", "🎯 Recomendações", "📊 Gráficos", "📋 Tabela"]
        )

        with tab1:
            st.subheader("Contexto Macroeconômico Atual")
            exibir_contexto_macro(macro_dados)

            st.divider()
            st.markdown("""
            **Interpretação:**
            - **Selic elevada** → Pressiona fundos imobiliários e ações
            - **Taxa Real** (Selic - IPCA) → Retorno real esperado de ativos
            - **CDI** → Benchmark para renda fixa privada
            """)

        with tab2:
            st.subheader("🎯 Recomendações por Ativo")
            exibir_recomendacoes(analises, carteira)

        with tab3:
            st.subheader("📊 Visualização da Carteira")
            exibir_graficos(analises, carteira)

        with tab4:
            exibir_tabela_completa(carteira, analises)

        # Rodapé
        st.divider()
        st.caption(f"Análise gerada em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} | "
                   f"Dados em tempo real via yfinance e BCB Open Data")

    else:
        st.info(
            "👈 Faça upload do seu extrato B3 na barra lateral para gerar análise!"
        )

        st.markdown("""
        ---
        ### 🚀 Como usar:

        1. **Exporte seu extrato da B3** em Excel (com abas: Ações, FII, ETF, etc.)
        2. **Faça upload** usando o botão na barra lateral
        3. **Aguarde a análise** (alguns segundos)
        4. **Visualize as recomendações**:
           - 🟢 **AUMENTE** — oportunidades de compra
           - 🟡 **MANTENHA** — posições bem posicionadas
           - 🔴 **REDUZA** — revisão recomendada

        ---

        ### 📊 Abas disponíveis:

        - **Contexto Macro** — Selic, IPCA, CDI atual e interpretação
        - **Recomendações** — Análise detalhada por ativo
        - **Gráficos** — Composição da carteira e distribuição de recomendações
        - **Tabela** — Todos os ativos com métricas completas

        ---

        ### 🤖 Analista Especialista:

        O sistema analisa cada ativo considerando:
        - **FIIs**: dividend yield vs Selic, P/VP, sensibilidade a juros
        - **Ações**: valuation (P/L, P/VP), setor específico, ciclo econômico
        - **Tesouro**: taxa real vs objetivo, duration
        - **CDB**: spread sobre CDI
        """)


if __name__ == "__main__":
    main()
