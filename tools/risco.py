"""
Análise de Risco — Sharpe e Sortino
Calcula métricas de risco ajustado para cada ativo da carteira
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from math import sqrt
from datetime import datetime

from tools.correlacao import calcular_correlacao
from tools.calculadores import CalculadoresFinanceiros


def calcular_metricas_risco(retornos_df: pd.DataFrame, cdi_anual: float) -> pd.DataFrame:
    """
    Calcula Sharpe e Sortino para cada ticker

    Args:
        retornos_df: DataFrame com retornos diários (linhas=datas, colunas=tickers)
        cdi_anual: CDI anual em percentual (ex: 14.40)

    Returns:
        DataFrame com colunas: Ticker, Retorno_1y, Volatilidade, Sharpe, Sortino, Classificacao
    """
    if retornos_df is None or retornos_df.empty:
        return None

    # Converter CDI anual para diário
    cdi_diario = (1 + cdi_anual / 100) ** (1 / 252) - 1

    dados = []

    for ticker in retornos_df.columns:
        serie = retornos_df[ticker]

        # Retorno médio anual
        retorno_medio_diario = serie.mean()
        retorno_anual = retorno_medio_diario * 252

        # Volatilidade anual (desvio padrão)
        volatilidade = serie.std() * sqrt(252)

        # Downside deviation (apenas retornos negativos)
        retornos_negativos = serie[serie < 0]
        if len(retornos_negativos) > 0:
            downside_dev = retornos_negativos.std() * sqrt(252)
        else:
            downside_dev = 0

        # Retorno excedente (acima de CDI)
        excesso_diario = retorno_medio_diario - cdi_diario
        excesso_anual = excesso_diario * 252

        # Sharpe Index
        sharpe = CalculadoresFinanceiros.calcular_sharpe(
            excesso_anual,
            volatilidade,
            taxa_livre_risco=0.0  # já é excesso
        ) if volatilidade > 0 else None

        # Sortino Index
        sortino = CalculadoresFinanceiros.calcular_sortino(
            excesso_anual,
            downside_dev,
            taxa_livre_risco=0.0
        ) if downside_dev > 0 else None

        # Classificação de Sharpe
        if sharpe is None:
            classificacao = "N/A"
        elif sharpe > 1.0:
            classificacao = "Excelente"
        elif sharpe > 0.5:
            classificacao = "Bom"
        elif sharpe >= 0.0:
            classificacao = "Aceitável"
        else:
            classificacao = "Ruim"

        dados.append({
            "Ticker": ticker,
            "Retorno_1y": round(retorno_anual * 100, 2),
            "Volatilidade": round(volatilidade * 100, 2),
            "Sharpe": round(sharpe, 3) if sharpe is not None else None,
            "Sortino": round(sortino, 3) if sortino is not None else None,
            "Classificacao": classificacao
        })

    df_risco = pd.DataFrame(dados)

    # Ordenar por Sharpe decrescente (NaN fica por último)
    df_risco = df_risco.sort_values(
        by="Sharpe",
        ascending=False,
        na_position="last"
    ).reset_index(drop=True)

    return df_risco


def calcular_risco_carteira(carteira: Dict, macro_dados: Dict) -> Optional[Dict]:
    """
    Orquestrador: calcula Sharpe/Sortino para todos os ativos da carteira

    Args:
        carteira: Dict retornado por ler_extrato_b3()
        macro_dados: Dict retornado por macro.obter_todas()

    Returns:
        Dict com {tabela_risco, n_ativos, cdi_usado, tickers_falha, timestamp}
        ou None se não há dados
    """
    # Obter retornos da correlação
    resultado_corr = calcular_correlacao(carteira)

    if resultado_corr is None:
        return None

    retornos_df = resultado_corr["retornos"]
    tickers_ok = resultado_corr["tickers_ok"]

    if len(tickers_ok) < 1:
        return None

    # Obter CDI para taxa livre de risco
    cdi = macro_dados.get("cdi", 13.65)

    # Calcular métricas
    df_risco = calcular_metricas_risco(retornos_df, cdi)

    if df_risco is None or df_risco.empty:
        return None

    return {
        "tabela_risco": df_risco,
        "n_ativos": len(tickers_ok),
        "cdi_usado": cdi,
        "tickers_falha": resultado_corr["tickers_falha"],
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Teste
    from tools.parser_b3 import ler_extrato_b3
    from tools.macro_data import macro

    print("Testando cálculo de Sharpe/Sortino...\n")

    carteira = ler_extrato_b3("posicao_2026.xlsx")
    macro_dados = macro.obter_todas()

    resultado = calcular_risco_carteira(carteira, macro_dados)

    if resultado:
        df = resultado["tabela_risco"]
        print(f"✓ {resultado['n_ativos']} ativos analisados")
        print(f"✓ CDI usado: {resultado['cdi_usado']:.2f}%\n")
        print(df.to_string(index=False))
    else:
        print("✗ Não foi possível calcular risco")
