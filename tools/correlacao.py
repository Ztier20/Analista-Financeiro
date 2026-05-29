"""
Análise de Correlação de Carteira
Calcula matriz de correlação entre ativos com dados de mercado
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import yfinance as yf
from datetime import datetime


CLASSES_ELEGÍVEIS = {"FII", "ACAO_BR", "BDR", "ETF_BR"}


def extrair_tickers_elegiveis(carteira: Dict) -> List[Dict]:
    """Filtra ativos com dados de mercado disponível"""
    tickers_unicos = set()
    resultado = []

    for classe, ativos in carteira.items():
        if classe not in CLASSES_ELEGÍVEIS:
            continue

        for ativo in ativos:
            ticker = ativo["ticker"]
            if ticker not in tickers_unicos:
                tickers_unicos.add(ticker)
                resultado.append({
                    "ticker": ticker,
                    "classe": classe
                })

    return resultado


def buscar_historico_precos(
    tickers_info: List[Dict],
    period: str = "1y"
) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Busca histórico de preços via yfinance
    Retorna (DataFrame de Close diário, lista de tickers que falharam)
    """
    if not tickers_info:
        return None, []

    # Montar lista de tickers com sufixo .SA
    tickers_yf = [f"{info['ticker']}.SA" for info in tickers_info]

    try:
        # Buscar histórico
        raw = yf.download(
            tickers_yf,
            period=period,
            auto_adjust=True,
            progress=False
        )

        if raw.empty:
            return None, tickers_yf

        # Extrair coluna Close
        # yfinance retorna MultiIndex se len(tickers) > 1, simples caso contrário
        if isinstance(raw.columns, pd.MultiIndex):
            close_df = raw["Close"]
        else:
            close_df = raw[["Close"]].rename(columns={"Close": tickers_yf[0]})

        # Remover sufixo .SA dos nomes de coluna
        close_df.columns = [col.replace(".SA", "") if isinstance(col, str) else col
                            for col in close_df.columns]

        # Identificar tickers que ficaram sem dados (colunas com todos NaN)
        tickers_falha = []
        for col in close_df.columns:
            if close_df[col].isna().all():
                tickers_falha.append(col)

        # Remover colunas sem dados
        close_df = close_df.dropna(axis=1, how="all")

        return close_df, tickers_falha

    except Exception as e:
        print(f"⚠️ Erro ao buscar histórico: {e}")
        return None, tickers_yf


def calcular_correlacao(carteira: Dict, period: str = "1y") -> Optional[Dict]:
    """
    Calcula matriz de correlação da carteira
    Retorna dict com matriz, retornos, metadados ou None se impossível
    """
    # Extrair tickers elegíveis
    tickers_info = extrair_tickers_elegiveis(carteira)

    if len(tickers_info) < 2:
        return None

    # Buscar histórico
    close_df, tickers_falha = buscar_historico_precos(tickers_info, period)

    if close_df is None or close_df.shape[1] < 2:
        return None

    # Inner join: manter apenas datas onde todos têm dados
    close_df = close_df.dropna(axis=0, how="any")

    if len(close_df) < 2:
        return None

    # Calcular retornos diários
    retornos = close_df.pct_change().dropna()

    if len(retornos) < 2:
        return None

    # Calcular matriz de correlação
    matriz = retornos.corr()

    # Tickers que realmente entraram na correlação
    tickers_ok = list(matriz.columns)

    return {
        "matriz": matriz,
        "retornos": retornos,
        "tickers_ok": tickers_ok,
        "tickers_falha": tickers_falha,
        "n_ativos": len(tickers_ok),
        "n_dias": len(retornos),
        "period": period,
        "timestamp": datetime.now().isoformat()
    }


def interpretar_correlacao(matriz: pd.DataFrame) -> Dict:
    """
    Extrai insights de correlação: pares, diversificação, etc.
    """
    if matriz is None or matriz.empty:
        return {}

    tickers = list(matriz.columns)
    n = len(tickers)

    # Extrair pares únicos (triângulo superior)
    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            val = float(matriz.iloc[i, j])
            pares.append({
                "Ativo A": tickers[i],
                "Ativo B": tickers[j],
                "Correlação": round(val, 3),
                "Abs": round(abs(val), 3)
            })

    # Ordenar por correlação absoluta
    df_pares = pd.DataFrame(pares).sort_values("Abs", ascending=False)

    # Filtrar pares especiais
    pares_alta_corr = df_pares[df_pares["Correlação"] > 0.85].to_dict("records")
    pares_corr_neg = df_pares[df_pares["Correlação"] < -0.3].to_dict("records")

    # Média de correlações absolutas (excluindo diagonal)
    import numpy as np
    mask = ~np.eye(n, dtype=bool)
    media_abs = float(np.abs(matriz.values[mask]).mean())

    return {
        "pares_alta_correlacao": pares_alta_corr,
        "pares_correlacao_negativa": pares_corr_neg,
        "media_correlacao_absoluta": round(media_abs, 3),
        "top_pares": df_pares
    }


if __name__ == "__main__":
    # Teste
    from tools.parser_b3 import ler_extrato_b3

    carteira = ler_extrato_b3("posicao_2026.xlsx")
    resultado = calcular_correlacao(carteira)

    if resultado:
        print(f"✓ {resultado['n_ativos']} ativos com dados")
        print(f"✓ {resultado['n_dias']} dias de histórico")
        print(f"\nMatriz de correlação:\n{resultado['matriz']}")

        interpretacao = interpretar_correlacao(resultado["matriz"])
        print(f"\nInterpretação:")
        print(f"  Correlação média absoluta: {interpretacao['media_correlacao_absoluta']:.3f}")
        print(f"  Pares com alta correlação (>0.85): {len(interpretacao['pares_alta_correlacao'])}")
        print(f"  Pares com correlação negativa (<-0.3): {len(interpretacao['pares_correlacao_negativa'])}")
    else:
        print("✗ Não foi possível calcular correlação")
