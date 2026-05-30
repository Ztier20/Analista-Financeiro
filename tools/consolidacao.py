"""
Análise Consolidada da Carteira
Concentração, alertas estratégicos, comparação com benchmarks
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd


def analisar_concentracao(carteira: Dict, relatorio_ativos: List[Dict]) -> Dict:
    """
    Calcula a concentração da carteira por classe e por ativo.

    Args:
        carteira: Dict retornado por ler_extrato_b3()
        relatorio_ativos: Lista de dicts com {ticker, classe, valor_total, score, recomendacao}

    Returns:
        Dict com {concentracao_por_classe, top_10_ativos, valor_total, metricas}
    """

    # Somar valor_total de cada ativo no relatorio
    df_ativos = pd.DataFrame(relatorio_ativos)

    if df_ativos.empty or "valor_total" not in df_ativos.columns:
        return None

    # Converter valor_total para float (pode vir como string ou NaN)
    df_ativos["valor_total"] = pd.to_numeric(df_ativos["valor_total"], errors="coerce")

    # Remover NaN e valores <= 0
    df_ativos = df_ativos.dropna(subset=["valor_total"])
    df_ativos = df_ativos[df_ativos["valor_total"] > 0]

    if df_ativos.empty:
        return None

    valor_total_carteira = df_ativos["valor_total"].sum()

    if valor_total_carteira <= 0:
        return None

    # Concentração por classe
    concentracao_por_classe = df_ativos.groupby("classe")["valor_total"].agg([
        ("valor", "sum"),
        ("quantidade", "count"),
        ("percentual", lambda x: (x.sum() / valor_total_carteira) * 100)
    ]).round(2).sort_values("valor", ascending=False)

    # Top 10 ativos
    top_10 = df_ativos.nlargest(10, "valor_total")[["ticker", "classe", "valor_total", "score"]].copy()
    top_10["percentual"] = (top_10["valor_total"] / valor_total_carteira * 100).round(2)

    # Concentração nos top 10
    conc_top10 = (top_10["valor_total"].sum() / valor_total_carteira) * 100

    # Concentração nos top 5
    conc_top5 = (df_ativos.nlargest(5, "valor_total")["valor_total"].sum() / valor_total_carteira) * 100

    # Concentração em 1 ativo
    conc_max = (df_ativos["valor_total"].max() / valor_total_carteira) * 100

    # Número de ativos por classe
    num_classes = len(concentracao_por_classe)
    num_ativos = len(df_ativos)

    return {
        "valor_total_carteira": round(valor_total_carteira, 2),
        "concentracao_por_classe": concentracao_por_classe,
        "top_10_ativos": top_10,
        "num_ativos": num_ativos,
        "num_classes": num_classes,
        "metricas": {
            "concentracao_top_1": round(conc_max, 2),
            "concentracao_top_5": round(conc_top5, 2),
            "concentracao_top_10": round(conc_top10, 2),
            "indice_herfindahl": round(((df_ativos["valor_total"] / valor_total_carteira) ** 2).sum() * 10000, 2)
        }
    }


def gerar_alertas_estrategicos(concentracao: Dict, relatorio_ativos: List[Dict], macro_dados: Dict) -> List[Dict]:
    """
    Gera alertas baseados em análise da carteira.

    Alertas:
    - Concentração excessiva (top 5 > 50%, top 1 > 30%)
    - Falta de diversificação por classe
    - Falta de renda variável vs renda fixa
    - Muitos ativos com score baixo
    - Todos os ativos com mesma recomendação

    Args:
        concentracao: Dict retornado por analisar_concentracao()
        relatorio_ativos: Lista de dicts com análises
        macro_dados: Dict com Selic, IPCA, CDI

    Returns:
        Lista de alertas: [{tipo, severidade, titulo, descricao, recomendacao}]
    """

    alertas = []

    if not concentracao:
        return alertas

    metricas = concentracao["metricas"]
    conc_por_classe = concentracao["concentracao_por_classe"]
    df_ativos = pd.DataFrame(relatorio_ativos)

    # ALERTA 1: Concentração em 1 ativo
    if metricas["concentracao_top_1"] > 30:
        alertas.append({
            "tipo": "concentracao_excessiva",
            "severidade": "CRÍTICA",
            "titulo": f"⚠️ Concentração Excessiva",
            "descricao": f"O maior ativo representa {metricas['concentracao_top_1']:.1f}% da carteira. Recomenda-se máximo 15%.",
            "recomendacao": "Rebalanceie ou reduza posição"
        })

    # ALERTA 2: Concentração em top 5
    if metricas["concentracao_top_5"] > 50:
        alertas.append({
            "tipo": "concentracao_top_5",
            "severidade": "ALTA",
            "titulo": "📊 Carteira Concentrada",
            "descricao": f"Os 5 maiores ativos representam {metricas['concentracao_top_5']:.1f}% da carteira.",
            "recomendacao": "Considere aumentar diversificação"
        })

    # ALERTA 3: Poucas classes
    if concentracao["num_classes"] < 3:
        alertas.append({
            "tipo": "poucos_tipos",
            "severidade": "MÉDIA",
            "titulo": "❌ Falta de Diversificação por Classe",
            "descricao": f"Carteira com apenas {concentracao['num_classes']} classe(s). Idealmente 4+.",
            "recomendacao": "Adicione outras classes (FII, ações, renda fixa, etc)"
        })

    # ALERTA 4: Desequilíbrio renda variável vs renda fixa
    rv_classes = ["FII", "ACAO_BR", "BDR", "ETF_BR"]
    rf_classes = ["TESOURO_IPCA", "TESOURO_SELIC", "TESOURO_PREFIXADO", "RENDA_FIXA_PRIVADA"]

    valor_rv = conc_por_classe[conc_por_classe.index.isin(rv_classes)]["valor"].sum()
    valor_rf = conc_por_classe[conc_por_classe.index.isin(rf_classes)]["valor"].sum()
    valor_total = concentracao["valor_total_carteira"]

    pct_rv = (valor_rv / valor_total * 100) if valor_total > 0 else 0
    pct_rf = (valor_rf / valor_total * 100) if valor_total > 0 else 0

    if pct_rv > 80 or pct_rv < 20:
        alertas.append({
            "tipo": "desequilibrio_rv_rf",
            "severidade": "MÉDIA",
            "titulo": "⚖️ Desequilíbrio RV vs RF",
            "descricao": f"Renda Variável: {pct_rv:.1f}% | Renda Fixa: {pct_rf:.1f}%",
            "recomendacao": "Rebalanceie para ~60% RV e ~40% RF (ou conforme seu perfil)"
        })

    # ALERTA 5: Muitos ativos com score baixo
    if "score" in df_ativos.columns:
        try:
            df_scores = pd.to_numeric(df_ativos["score"], errors="coerce")
            ativos_baixo_score = (df_scores < 4).sum()

            if ativos_baixo_score > len(df_ativos) * 0.3:  # Mais de 30% com score < 4
                alertas.append({
                    "tipo": "qualidade_baixa",
                    "severidade": "ALTA",
                    "titulo": "📉 Qualidade Baixa de Ativos",
                    "descricao": f"{ativos_baixo_score} ativos têm score < 4. Qualidade comprometida.",
                    "recomendacao": "Revise e considere substituir ativos de baixa qualidade"
                })
        except:
            pass

    # ALERTA 6: Todos com mesma recomendação
    if "recomendacao" in df_ativos.columns:
        recs = df_ativos["recomendacao"].value_counts()
        if len(recs) == 1:
            rec_unica = recs.index[0]
            alertas.append({
                "tipo": "recomendacao_unica",
                "severidade": "MÉDIA",
                "titulo": "🎯 Falta Diversidade de Recomendações",
                "descricao": f"Todos os ativos têm recomendação '{rec_unica}'. Carteira pode estar desequilibrada.",
                "recomendacao": "Revise se isso reflete a realidade ou se há viés na análise"
            })

    # ALERTA 7: Muitas REDUZA/VENDA
    if "recomendacao" in df_ativos.columns:
        reduzas = (df_ativos["recomendacao"] == "REDUZA").sum()
        vendas = (df_ativos["recomendacao"] == "VENDA").sum()
        total_recs = len(df_ativos)

        if (reduzas + vendas) > total_recs * 0.4:
            alertas.append({
                "tipo": "muitos_reduzas",
                "severidade": "ALTA",
                "titulo": "⚠️ Muitos Ativos para Reduzir",
                "descricao": f"{reduzas} REDUZAs + {vendas} VENDAs em {total_recs} ativos.",
                "recomendacao": "Considere reavaliação estratégica da carteira ou atualização dos critérios"
            })

    return alertas


def gerar_resumo_consolidado(concentracao: Dict, alertas: List[Dict], carteira: Dict) -> str:
    """
    Gera um resumo textual consolidado para o relatório markdown.
    """

    if not concentracao:
        return "## 📋 Análise Consolidada\n\n❌ Dados insuficientes para análise consolidada.\n\n"

    md = "## 📋 Análise Consolidada da Carteira\n\n"

    # Seção 1: Visão Geral
    md += "### 📊 Visão Geral\n\n"
    md += f"- **Total de Ativos:** {concentracao['num_ativos']}\n"
    md += f"- **Classes Representadas:** {concentracao['num_classes']}\n"
    md += f"- **Valor Total da Carteira:** R$ {concentracao['valor_total_carteira']:,.2f}\n\n"

    # Seção 2: Concentração por Classe
    md += "### 💼 Concentração por Classe\n\n"
    md += "| Classe | Valor | Quantidade | % Carteira |\n"
    md += "|---|---|---|---|\n"

    conc = concentracao["concentracao_por_classe"]
    for classe in conc.index:
        row = conc.loc[classe]
        md += f"| {classe} | R$ {row['valor']:,.2f} | {int(row['quantidade'])} | {row['percentual']:.1f}% |\n"

    md += "\n"

    # Seção 3: Top 10 Ativos
    md += "### 🏆 Top 10 Maiores Posições\n\n"
    md += "| # | Ticker | Classe | Valor | % | Score |\n"
    md += "|---|---|---|---|---|---|\n"

    top10 = concentracao["top_10_ativos"]
    for idx, (_, row) in enumerate(top10.iterrows(), 1):
        score = f"{row['score']:.1f}" if pd.notna(row['score']) else "N/A"
        md += f"| {idx} | {row['ticker']} | {row['classe']} | R$ {row['valor_total']:,.2f} | {row['percentual']:.1f}% | {score} |\n"

    md += "\n"

    # Seção 4: Métricas de Concentração
    md += "### 📈 Métricas de Concentração\n\n"
    metricas = concentracao["metricas"]
    md += f"- **Maior Posição (Top 1):** {metricas['concentracao_top_1']:.1f}%\n"
    md += f"- **Top 5:** {metricas['concentracao_top_5']:.1f}%\n"
    md += f"- **Top 10:** {metricas['concentracao_top_10']:.1f}%\n"
    md += f"- **Índice de Herfindahl:** {metricas['indice_herfindahl']:.0f}\n"
    md += "  *(0 = diversificação perfeita, 10000 = concentração máxima)*\n\n"

    # Seção 5: Alertas
    if alertas:
        md += "### ⚠️ Alertas Estratégicos\n\n"

        for alerta in alertas:
            severidade_emoji = {
                "CRÍTICA": "🔴",
                "ALTA": "🟠",
                "MÉDIA": "🟡",
                "BAIXA": "🟢"
            }.get(alerta["severidade"], "⚪")

            md += f"**{severidade_emoji} {alerta['titulo']}** ({alerta['severidade']})\n\n"
            md += f"{alerta['descricao']}\n\n"
            md += f"*Recomendação: {alerta['recomendacao']}*\n\n"
    else:
        md += "### ✅ Nenhum Alerta Crítico\n\n"
        md += "A carteira apresenta boa estrutura de diversificação.\n\n"

    return md


if __name__ == "__main__":
    from tools.parser_b3 import ler_extrato_b3
    from tools.macro_data import macro

    # Teste
    carteira = ler_extrato_b3("posicao_2026.xlsx")
    macro_dados = macro.obter_todas()

    # Simular relatorio_ativos (normalmente vem do relatorio.py)
    relatorio_ativos = []
    for classe, ativos in carteira.items():
        for ativo in ativos:
            relatorio_ativos.append({
                "ticker": ativo["ticker"],
                "classe": ativo["classe"],
                "valor_total": ativo.get("valor_total", 0),
                "score": 6.5,
                "recomendacao": "MANTENHA"
            })

    conc = analisar_concentracao(carteira, relatorio_ativos)
    alertas = gerar_alertas_estrategicos(conc, relatorio_ativos, macro_dados)

    print(gerar_resumo_consolidado(conc, alertas, carteira))
