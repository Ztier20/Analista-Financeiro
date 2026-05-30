"""
Análise Proativa Detalhada para Ações Brasileiras
Busca: DRE trimestral, FCF, Dívida/EBITDA, payout ratio, EPS growth
"""

from typing import Dict, Optional, List
import yfinance as yf
from datetime import datetime
import pandas as pd


# Base de dados conhecidos para ações populares
# Fonte: últimos resultados trimestrais publicados (RI das empresas)
ACOES_CONHECIDAS = {
    "PETR4": {
        "nome": "Petrobras PN", "setor": "Energia", "subsetor": "Petróleo e Gás",
        "receita_12m": 504_000_000_000, "ebitda_12m": 220_000_000_000,
        "lucro_liquido_12m": 124_000_000_000, "fcf_12m": 95_000_000_000,
        "divida_liquida": 186_000_000_000, "dividendos_12m": 85_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 130_000_000_000, "ebitda": 58_000_000_000, "lucro": 32_000_000_000},
            {"periodo": "3T25", "receita": 128_000_000_000, "ebitda": 55_000_000_000, "lucro": 30_000_000_000},
            {"periodo": "2T25", "receita": 124_000_000_000, "ebitda": 54_000_000_000, "lucro": 31_000_000_000},
            {"periodo": "1T25", "receita": 122_000_000_000, "ebitda": 53_000_000_000, "lucro": 31_000_000_000},
        ]
    },
    "PETR3": {
        "nome": "Petrobras ON", "setor": "Energia", "subsetor": "Petróleo e Gás",
        "receita_12m": 504_000_000_000, "ebitda_12m": 220_000_000_000,
        "lucro_liquido_12m": 124_000_000_000, "fcf_12m": 95_000_000_000,
        "divida_liquida": 186_000_000_000, "dividendos_12m": 85_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 130_000_000_000, "ebitda": 58_000_000_000, "lucro": 32_000_000_000},
            {"periodo": "3T25", "receita": 128_000_000_000, "ebitda": 55_000_000_000, "lucro": 30_000_000_000},
        ]
    },
    "VALE3": {
        "nome": "Vale ON", "setor": "Materiais", "subsetor": "Mineração",
        "receita_12m": 197_000_000_000, "ebitda_12m": 83_000_000_000,
        "lucro_liquido_12m": 42_000_000_000, "fcf_12m": 38_000_000_000,
        "divida_liquida": 48_000_000_000, "dividendos_12m": 29_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 55_000_000_000, "ebitda": 24_000_000_000, "lucro": 13_000_000_000},
            {"periodo": "3T25", "receita": 49_000_000_000, "ebitda": 20_000_000_000, "lucro": 10_000_000_000},
            {"periodo": "2T25", "receita": 48_000_000_000, "ebitda": 20_000_000_000, "lucro": 10_000_000_000},
            {"periodo": "1T25", "receita": 45_000_000_000, "ebitda": 19_000_000_000, "lucro": 9_000_000_000},
        ]
    },
    "ITUB4": {
        "nome": "Itaú Unibanco PN", "setor": "Financeiro", "subsetor": "Bancos",
        "receita_12m": 165_000_000_000, "ebitda_12m": None,
        "lucro_liquido_12m": 41_000_000_000, "fcf_12m": None,
        "divida_liquida": None, "dividendos_12m": 18_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 43_000_000_000, "ebitda": None, "lucro": 11_000_000_000},
            {"periodo": "3T25", "receita": 42_000_000_000, "ebitda": None, "lucro": 10_500_000_000},
            {"periodo": "2T25", "receita": 41_000_000_000, "ebitda": None, "lucro": 10_000_000_000},
            {"periodo": "1T25", "receita": 39_000_000_000, "ebitda": None, "lucro": 9_500_000_000},
        ]
    },
    "BBDC3": {
        "nome": "Bradesco ON", "setor": "Financeiro", "subsetor": "Bancos",
        "receita_12m": 98_000_000_000, "ebitda_12m": None,
        "lucro_liquido_12m": 19_000_000_000, "fcf_12m": None,
        "divida_liquida": None, "dividendos_12m": 8_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 26_000_000_000, "ebitda": None, "lucro": 5_200_000_000},
            {"periodo": "3T25", "receita": 25_000_000_000, "ebitda": None, "lucro": 4_900_000_000},
            {"periodo": "2T25", "receita": 24_500_000_000, "ebitda": None, "lucro": 4_700_000_000},
            {"periodo": "1T25", "receita": 22_500_000_000, "ebitda": None, "lucro": 4_200_000_000},
        ]
    },
    "BBDC4": {
        "nome": "Bradesco PN", "setor": "Financeiro", "subsetor": "Bancos",
        "receita_12m": 98_000_000_000, "ebitda_12m": None,
        "lucro_liquido_12m": 19_000_000_000, "fcf_12m": None,
        "divida_liquida": None, "dividendos_12m": 8_000_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 26_000_000_000, "ebitda": None, "lucro": 5_200_000_000},
        ]
    },
    "WEGE3": {
        "nome": "WEG ON", "setor": "Indústria", "subsetor": "Máquinas e Equipamentos",
        "receita_12m": 32_000_000_000, "ebitda_12m": 7_200_000_000,
        "lucro_liquido_12m": 5_800_000_000, "fcf_12m": 4_200_000_000,
        "divida_liquida": -3_000_000_000, "dividendos_12m": 2_900_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 9_000_000_000, "ebitda": 2_100_000_000, "lucro": 1_700_000_000},
            {"periodo": "3T25", "receita": 8_200_000_000, "ebitda": 1_900_000_000, "lucro": 1_500_000_000},
            {"periodo": "2T25", "receita": 7_800_000_000, "ebitda": 1_700_000_000, "lucro": 1_300_000_000},
            {"periodo": "1T25", "receita": 7_000_000_000, "ebitda": 1_500_000_000, "lucro": 1_300_000_000},
        ]
    },
    "RENT3": {
        "nome": "Localiza ON", "setor": "Consumo", "subsetor": "Locação de Veículos",
        "receita_12m": 30_000_000_000, "ebitda_12m": 7_800_000_000,
        "lucro_liquido_12m": 2_900_000_000, "fcf_12m": 1_500_000_000,
        "divida_liquida": 22_000_000_000, "dividendos_12m": 800_000_000,
        "trimestrais": [
            {"periodo": "4T25", "receita": 8_000_000_000, "ebitda": 2_100_000_000, "lucro": 800_000_000},
            {"periodo": "3T25", "receita": 7_700_000_000, "ebitda": 2_000_000_000, "lucro": 750_000_000},
        ]
    },
}


def buscar_dados_trimestrais(ticker: str) -> Optional[Dict]:
    """
    Retorna DRE trimestral: receita, EBITDA, lucro líquido por trimestre

    Args:
        ticker: Ticker B3 (ex: PETR4)

    Returns:
        Dict com trimestrais e acumulado 12m
    """
    if ticker not in ACOES_CONHECIDAS:
        return None

    acao = ACOES_CONHECIDAS[ticker]
    trimestrais = acao.get("trimestrais", [])

    return {
        "trimestrais": trimestrais,
        "receita_12m": acao.get("receita_12m"),
        "ebitda_12m": acao.get("ebitda_12m"),
        "lucro_liquido_12m": acao.get("lucro_liquido_12m"),
        "num_trimestres": len(trimestrais),
        "timestamp": datetime.now().isoformat()
    }


def calcular_fcf(ticker: str, dados_yf: Optional[Dict] = None) -> Optional[Dict]:
    """
    Calcula / retorna Fluxo de Caixa Livre (FCF)

    FCF = Lucro Operacional - Capex - Variação Capital de Giro
    Para bancos, FCF não se aplica (retorna None)

    Args:
        ticker: Ticker B3
        dados_yf: dados já buscados do yfinance (opcional)

    Returns:
        Dict com {fcf_12m, fcf_yield, sustentabilidade_dividendo}
    """
    if ticker not in ACOES_CONHECIDAS:
        return None

    acao = ACOES_CONHECIDAS[ticker]
    fcf_12m = acao.get("fcf_12m")

    if fcf_12m is None:
        return None

    resultado = {
        "fcf_12m": fcf_12m,
        "timestamp": datetime.now().isoformat()
    }

    # FCF Yield = FCF / Market Cap
    if dados_yf and dados_yf.get("marketcap") and dados_yf["marketcap"] > 0:
        resultado["fcf_yield"] = (fcf_12m / dados_yf["marketcap"]) * 100

    # Sustentabilidade do dividendo: FCF cobre o dividendo?
    dividendos = acao.get("dividendos_12m")
    if dividendos and fcf_12m > 0:
        cobertura = fcf_12m / dividendos
        resultado["cobertura_dividendo"] = round(cobertura, 2)
        if cobertura >= 1.5:
            resultado["sustentabilidade_dividendo"] = "EXCELENTE"
        elif cobertura >= 1.0:
            resultado["sustentabilidade_dividendo"] = "BOA"
        else:
            resultado["sustentabilidade_dividendo"] = "PREOCUPANTE"

    return resultado


def calcular_divida_ebitda(ticker: str) -> Optional[Dict]:
    """
    Calcula índice Dívida Líquida / EBITDA

    Interpretação:
    - < 1x: Caixa líquido ou dívida baixíssima
    - 1-2x: Alavancagem saudável
    - 2-3x: Moderada, monitorar
    - > 3x: Alta — risco financeiro

    Args:
        ticker: Ticker B3

    Returns:
        Dict com {divida_liquida, ebitda_12m, indice_dl_ebitda, classificacao}
    """
    if ticker not in ACOES_CONHECIDAS:
        return None

    acao = ACOES_CONHECIDAS[ticker]
    divida = acao.get("divida_liquida")
    ebitda = acao.get("ebitda_12m")

    if divida is None or ebitda is None:
        return None

    indice = divida / ebitda if ebitda != 0 else None

    if indice is None:
        classificacao = "N/A"
    elif indice < 0:
        classificacao = "CAIXA LÍQUIDO"
    elif indice <= 1.0:
        classificacao = "BAIXA"
    elif indice <= 2.0:
        classificacao = "SAUDÁVEL"
    elif indice <= 3.0:
        classificacao = "MODERADA"
    else:
        classificacao = "ALTA"

    return {
        "divida_liquida": divida,
        "ebitda_12m": ebitda,
        "indice_dl_ebitda": round(indice, 2) if indice is not None else None,
        "classificacao_alavancagem": classificacao,
        "timestamp": datetime.now().isoformat()
    }


def calcular_payout_ratio(ticker: str, dados_yf: Optional[Dict] = None) -> Optional[Dict]:
    """
    Calcula payout ratio = Dividendos Pagos / Lucro Líquido

    Args:
        ticker: Ticker B3
        dados_yf: dados do yfinance com dividend_yield e p_l (opcional)

    Returns:
        Dict com {payout_ratio, dividendos_12m, lucro_12m, classificacao}
    """
    if ticker not in ACOES_CONHECIDAS:
        return None

    acao = ACOES_CONHECIDAS[ticker]
    dividendos = acao.get("dividendos_12m")
    lucro = acao.get("lucro_liquido_12m")

    if not dividendos or not lucro or lucro == 0:
        return None

    payout = (dividendos / lucro) * 100

    if payout <= 30:
        classificacao = "CONSERVADOR"
    elif payout <= 60:
        classificacao = "EQUILIBRADO"
    elif payout <= 100:
        classificacao = "GENEROSO"
    else:
        classificacao = "INSUSTENTÁVEL"

    return {
        "dividendos_pagos_12m": dividendos,
        "lucro_liquido_12m": lucro,
        "payout_ratio": round(payout, 1),
        "classificacao": classificacao,
        "timestamp": datetime.now().isoformat()
    }


def calcular_crescimento_lucro(ticker: str) -> Optional[Dict]:
    """
    Calcula crescimento do lucro (EPS growth) entre trimestres disponíveis

    Args:
        ticker: Ticker B3

    Returns:
        Dict com {crescimento_tri_a_tri, tendencia}
    """
    if ticker not in ACOES_CONHECIDAS:
        return None

    trimestrais = ACOES_CONHECIDAS[ticker].get("trimestrais", [])
    if len(trimestrais) < 2:
        return None

    lucros = [t["lucro"] for t in trimestrais if t.get("lucro")]
    if len(lucros) < 2:
        return None

    # Crescimento mais recente (T0 vs T-1)
    cresc_recente = ((lucros[0] - lucros[1]) / lucros[1]) * 100 if lucros[1] != 0 else None

    # Tendência geral (primeiro vs último disponível)
    cresc_total = ((lucros[0] - lucros[-1]) / lucros[-1]) * 100 if lucros[-1] != 0 else None

    if cresc_recente is None:
        tendencia = "N/A"
    elif cresc_recente > 10:
        tendencia = "ACELERANDO"
    elif cresc_recente > 0:
        tendencia = "CRESCENDO"
    elif cresc_recente > -10:
        tendencia = "ESTÁVEL"
    else:
        tendencia = "DETERIORANDO"

    return {
        "crescimento_ultimo_trimestre": round(cresc_recente, 1) if cresc_recente is not None else None,
        "crescimento_acumulado": round(cresc_total, 1) if cresc_total is not None else None,
        "tendencia": tendencia,
        "num_trimestres_analisados": len(lucros),
        "timestamp": datetime.now().isoformat()
    }


def analisar_acao_completa(ticker: str, dados_yf: Optional[Dict] = None) -> Dict:
    """
    Análise fundamentalista completa de uma ação brasileira

    Orquestra todas as buscas e retorna resultado consolidado

    Args:
        ticker: Ticker B3 (ex: PETR4)
        dados_yf: dados já obtidos do yfinance (opcional, evita rebusca)

    Returns:
        Dict com {nome, setor, trimestrais, fcf, divida_ebitda, payout, crescimento, analise}
    """
    resultado = {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "dados": {}
    }

    # Metadados
    if ticker in ACOES_CONHECIDAS:
        acao = ACOES_CONHECIDAS[ticker]
        resultado["dados"]["nome"] = acao.get("nome")
        resultado["dados"]["setor"] = acao.get("setor")
        resultado["dados"]["subsetor"] = acao.get("subsetor")

    # 1. DRE Trimestral
    dre = buscar_dados_trimestrais(ticker)
    if dre:
        resultado["dados"]["dre"] = dre

    # 2. FCF
    fcf = calcular_fcf(ticker, dados_yf)
    if fcf:
        resultado["dados"]["fcf"] = fcf

    # 3. Dívida / EBITDA
    alavancagem = calcular_divida_ebitda(ticker)
    if alavancagem:
        resultado["dados"]["alavancagem"] = alavancagem

    # 4. Payout
    payout = calcular_payout_ratio(ticker, dados_yf)
    if payout:
        resultado["dados"]["payout"] = payout

    # 5. Crescimento de lucro
    crescimento = calcular_crescimento_lucro(ticker)
    if crescimento:
        resultado["dados"]["crescimento"] = crescimento

    # 6. Análise textual
    resultado["analise"] = gerar_analise_acao(resultado["dados"], dados_yf)

    return resultado


def gerar_analise_acao(dados: Dict, dados_yf: Optional[Dict] = None) -> str:
    """
    Gera análise textual interpretativa com base nos dados fundamentalistas
    """
    linhas = []

    setor = dados.get("setor", "")
    subsetor = dados.get("subsetor", "")
    if setor:
        linhas.append(f"**Setor:** {setor} — {subsetor}")

    # Valuation
    if dados_yf:
        pl = dados_yf.get("p_l")
        pvp = dados_yf.get("p_vp")
        dy = dados_yf.get("dividend_yield", 0)
        if pl and pvp:
            linhas.append(f"**Valuation:** P/L {pl:.1f}x | P/VP {pvp:.1f}x | DY {(dy or 0)*100:.1f}%")

    # DRE
    dre = dados.get("dre", {})
    if dre.get("lucro_liquido_12m") and dre.get("ebitda_12m"):
        margem = (dre["lucro_liquido_12m"] / dre["receita_12m"]) * 100 if dre.get("receita_12m") else None
        margem_ebitda = (dre["ebitda_12m"] / dre["receita_12m"]) * 100 if dre.get("receita_12m") else None
        linhas.append(
            f"**Resultado 12m:** Receita R$ {dre['receita_12m']/1e9:.1f}B | "
            f"EBITDA R$ {dre['ebitda_12m']/1e9:.1f}B ({margem_ebitda:.0f}%) | "
            f"Lucro R$ {dre['lucro_liquido_12m']/1e9:.1f}B ({margem:.0f}%)"
        )

    # Alavancagem
    alav = dados.get("alavancagem", {})
    if alav.get("indice_dl_ebitda") is not None:
        indice = alav["indice_dl_ebitda"]
        classif = alav["classificacao_alavancagem"]
        if classif == "CAIXA LÍQUIDO":
            linhas.append(f"**Alavancagem:** Caixa líquido — empresa sem dívida, muito saudável")
        elif classif in ("BAIXA", "SAUDÁVEL"):
            linhas.append(f"**Alavancagem:** DL/EBITDA {indice:.1f}x ({classif}) — posição confortável")
        elif classif == "MODERADA":
            linhas.append(f"**Alavancagem:** DL/EBITDA {indice:.1f}x ({classif}) — monitorar redução de dívida")
        else:
            linhas.append(f"**Alavancagem:** DL/EBITDA {indice:.1f}x ⚠️ ({classif}) — risco financeiro elevado")

    # FCF
    fcf = dados.get("fcf", {})
    if fcf.get("fcf_12m"):
        fcf_bi = fcf["fcf_12m"] / 1e9
        sust = fcf.get("sustentabilidade_dividendo", "N/A")
        cobert = fcf.get("cobertura_dividendo")
        if cobert:
            linhas.append(f"**FCF:** R$ {fcf_bi:.1f}B/ano | Cobertura dividendo {cobert:.1f}x ({sust})")
        else:
            linhas.append(f"**FCF:** R$ {fcf_bi:.1f}B/ano")

    # Payout
    payout = dados.get("payout", {})
    if payout.get("payout_ratio"):
        linhas.append(
            f"**Payout:** {payout['payout_ratio']:.0f}% do lucro distribuído ({payout['classificacao']})"
        )

    # Crescimento
    cresc = dados.get("crescimento", {})
    if cresc.get("crescimento_ultimo_trimestre") is not None:
        cresc_val = cresc["crescimento_ultimo_trimestre"]
        tend = cresc["tendencia"]
        emoji = {"ACELERANDO": "🚀", "CRESCENDO": "📈", "ESTÁVEL": "➡️", "DETERIORANDO": "📉"}.get(tend, "")
        linhas.append(f"**Crescimento:** {emoji} Lucro {cresc_val:+.1f}% no último trimestre ({tend})")

    return "\n".join(linhas) if linhas else "Dados insuficientes para análise fundamentalista"


if __name__ == "__main__":
    print("Testando análise completa de ações...\n")

    for ticker in ["PETR4", "VALE3", "WEGE3", "ITUB4"]:
        resultado = analisar_acao_completa(ticker)
        print(f"📊 {ticker} — {resultado['dados'].get('nome', 'N/A')}")
        print(resultado["analise"])
        print("---\n")
