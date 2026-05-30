"""
Alertas em Tempo Real
Detecta mudanças relevantes nos scores e condições de mercado
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

from tools.historico import calcular_variacao_scores, buscar_ultima_analise


def gerar_alertas_tempo_real(
    analises: Dict,
    macro_dados: Dict,
    variacao_minima_pct: float = 10.0
) -> List[Dict]:
    """
    Gera lista de alertas baseados no estado atual da carteira

    Args:
        analises: resultado do processar_carteira do dashboard
        macro_dados: selic, ipca_12m, cdi
        variacao_minima_pct: % mínimo de queda para gerar alerta de score

    Returns:
        Lista de alertas ordenados por severidade
    """
    alertas = []
    selic = macro_dados.get("selic", 14.4)
    cdi   = macro_dados.get("cdi", 14.35)

    # ── 1. Score baixo (< 3) ──────────────────────────────────────────────
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score_info = ativo.get("score", {})
            score = score_info.get("score") if isinstance(score_info, dict) else score_info
            try:
                score = float(score)
            except (TypeError, ValueError):
                continue

            if score < 3:
                alertas.append({
                    "tipo": "SCORE_CRITICO",
                    "severidade": "CRÍTICA",
                    "ticker": ativo["ticker"],
                    "classe": classe,
                    "titulo": f"Score crítico — {ativo['ticker']}",
                    "descricao": f"Score {score:.1f}/10 — ativo em situação crítica",
                    "recomendacao": "Avalie redução ou saída da posição",
                    "valor": score,
                })
            elif score < 5:
                alertas.append({
                    "tipo": "SCORE_FRACO",
                    "severidade": "ALTA",
                    "ticker": ativo["ticker"],
                    "classe": classe,
                    "titulo": f"Score fraco — {ativo['ticker']}",
                    "descricao": f"Score {score:.1f}/10 — abaixo do neutro",
                    "recomendacao": "Monitore de perto; considere redução",
                    "valor": score,
                })

    # ── 2. FII com DY abaixo da Selic ────────────────────────────────────
    for classe, ativos_lista in analises.items():
        if classe != "FII":
            continue
        for ativo in ativos_lista:
            dy = ativo.get("dados_yf", {}).get("dividend_yield_12m", 0) or 0
            if dy == 0:
                # Tentar via fii_proativo
                dy = ativo.get("dados_yf", {}).get("dividend_yield", 0) or 0
                if dy:
                    dy = dy * 100
            if dy > 0 and dy < selic:
                diferenca = selic - dy
                alertas.append({
                    "tipo": "FII_DY_ABAIXO_SELIC",
                    "severidade": "ALTA",
                    "ticker": ativo["ticker"],
                    "classe": "FII",
                    "titulo": f"DY abaixo da Selic — {ativo['ticker']}",
                    "descricao": f"DY {dy:.1f}% < Selic {selic:.1f}% (diferença de {diferenca:.1f}pp)",
                    "recomendacao": "FII não remunera acima da taxa livre de risco — reavalie a posição",
                    "valor": dy,
                })

    # ── 3. Variação de score desde última análise ─────────────────────────
    try:
        variacoes = calcular_variacao_scores()
        if not variacoes.empty:
            for _, row in variacoes.iterrows():
                var_pct = row.get("variacao_pct")
                variacao = row.get("variacao")
                if pd.isna(var_pct) or pd.isna(variacao):
                    continue
                if var_pct <= -variacao_minima_pct:
                    alertas.append({
                        "tipo": "SCORE_CAIU",
                        "severidade": "ALTA" if var_pct <= -20 else "MÉDIA",
                        "ticker": row["ticker"],
                        "classe": row["classe"],
                        "titulo": f"Score caiu — {row['ticker']}",
                        "descricao": (
                            f"Score caiu {abs(variacao):.1f} pontos ({var_pct:.0f}%) "
                            f"desde a última análise"
                        ),
                        "recomendacao": "Verifique o que mudou no ativo",
                        "valor": variacao,
                    })
                elif var_pct >= variacao_minima_pct:
                    alertas.append({
                        "tipo": "SCORE_SUBIU",
                        "severidade": "BAIXA",
                        "ticker": row["ticker"],
                        "classe": row["classe"],
                        "titulo": f"Score melhorou — {row['ticker']}",
                        "descricao": (
                            f"Score subiu {variacao:.1f} pontos (+{var_pct:.0f}%) "
                            f"desde a última análise"
                        ),
                        "recomendacao": "Oportunidade de aumento de posição",
                        "valor": variacao,
                    })
    except Exception:
        pass

    # ── 4. Ação em sobrecompra (P/L > 25) ────────────────────────────────
    for classe, ativos_lista in analises.items():
        if classe != "ACAO_BR":
            continue
        for ativo in ativos_lista:
            pl = ativo.get("dados_yf", {}).get("p_l")
            if pl and pl > 25:
                alertas.append({
                    "tipo": "ACAO_SOBRECOMPRADA",
                    "severidade": "MÉDIA",
                    "ticker": ativo["ticker"],
                    "classe": "ACAO_BR",
                    "titulo": f"Valuation esticado — {ativo['ticker']}",
                    "descricao": f"P/L {pl:.1f}x — acima de 25x considerado caro",
                    "recomendacao": "Verifique se o crescimento justifica o múltiplo",
                    "valor": pl,
                })

    # ── 5. Concentração excessiva em único ativo ─────────────────────────
    total_valor = sum(
        a.get("valor", 0)
        for ativos_lista in analises.values()
        for a in ativos_lista
    )
    if total_valor > 0:
        for classe, ativos_lista in analises.items():
            for ativo in ativos_lista:
                pct = (ativo.get("valor", 0) / total_valor) * 100
                if pct > 20:
                    alertas.append({
                        "tipo": "CONCENTRACAO_EXCESSIVA",
                        "severidade": "CRÍTICA" if pct > 30 else "ALTA",
                        "ticker": ativo["ticker"],
                        "classe": classe,
                        "titulo": f"Concentração excessiva — {ativo['ticker']}",
                        "descricao": f"{pct:.1f}% da carteira em um único ativo",
                        "recomendacao": "Considere reduzir para abaixo de 15%",
                        "valor": pct,
                    })

    # ── 6. Renda fixa abaixo do CDI ──────────────────────────────────────
    for classe, ativos_lista in analises.items():
        if "RF_" not in classe and "TESOURO" not in classe:
            continue
        for ativo in ativos_lista:
            rf = ativo.get("dados_yf", {}).get("rf_proativo", {})
            taxa = rf.get("taxa_contratada") if rf else None
            indexador = rf.get("classificacao", {}).get("indexador") if rf else None
            if taxa and indexador == "CDI" and taxa < cdi * 0.90:
                alertas.append({
                    "tipo": "RF_ABAIXO_CDI",
                    "severidade": "MÉDIA",
                    "ticker": ativo["ticker"],
                    "classe": classe,
                    "titulo": f"Renda fixa abaixo do CDI — {ativo['ticker']}",
                    "descricao": f"Taxa {taxa:.2f}% < 90% do CDI ({cdi*0.9:.2f}%)",
                    "recomendacao": "Avalie migração para título com melhor spread",
                    "valor": taxa,
                })

    # Ordenar: CRÍTICA > ALTA > MÉDIA > BAIXA
    ordem = {"CRÍTICA": 0, "ALTA": 1, "MÉDIA": 2, "BAIXA": 3}
    alertas.sort(key=lambda x: ordem.get(x["severidade"], 9))

    return alertas


def resumo_alertas(alertas: List[Dict]) -> Dict:
    """Retorna contagem de alertas por severidade"""
    contagem = {"CRÍTICA": 0, "ALTA": 0, "MÉDIA": 0, "BAIXA": 0}
    for a in alertas:
        sev = a.get("severidade", "BAIXA")
        contagem[sev] = contagem.get(sev, 0) + 1
    return contagem
