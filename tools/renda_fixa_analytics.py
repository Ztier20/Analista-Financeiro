"""
Análise Proativa Detalhada para Renda Fixa
Busca: duration, spread sobre CDI/IPCA, posição na curva, risco de crédito
Cobre: Tesouro Direto, CDB, LCI, LCA, CRI, CRA, Debêntures, FIDC
"""

from typing import Dict, Optional, List
from datetime import datetime
import requests


# ── Ratings de crédito por emissor ──────────────────────────────────────────
RATINGS_EMISSORES = {
    # Grandes bancos — investment grade máximo
    "ITAU": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Banco Grande"},
    "BRADESCO": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Banco Grande"},
    "SANTANDER": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Banco Grande"},
    "CAIXA": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Banco Público"},
    "BB": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Banco Público"},
    "BTG": {"rating": "AA+", "perspectiva": "Positiva", "tipo": "Banco Médio"},
    "XP": {"rating": "AA", "perspectiva": "Estável", "tipo": "Banco Médio"},
    "NUBANK": {"rating": "AA", "perspectiva": "Positiva", "tipo": "Fintech"},
    # Bancos médios — risco um pouco maior, spreads melhores
    "INTER": {"rating": "A+", "perspectiva": "Estável", "tipo": "Banco Médio"},
    "C6": {"rating": "A", "perspectiva": "Estável", "tipo": "Fintech"},
    "DAYCOVAL": {"rating": "AA-", "perspectiva": "Estável", "tipo": "Banco Médio"},
    "PINE": {"rating": "BBB+", "perspectiva": "Estável", "tipo": "Banco Médio"},
    "MERCANTIL": {"rating": "A-", "perspectiva": "Estável", "tipo": "Banco Médio"},
    # Governo — risco soberano
    "TESOURO": {"rating": "AAA", "perspectiva": "Estável", "tipo": "Soberano"},
}

# ── Curva de juros DI futuro (referência) ────────────────────────────────────
# Dados aproximados — em produção viriam da B3/Anbima
CURVA_DI_REFERENCIA = {
    "1m":   14.40,
    "3m":   14.35,
    "6m":   14.20,
    "1a":   13.80,
    "2a":   13.20,
    "3a":   12.90,
    "5a":   12.60,
    "10a":  12.40,
}

# ── Spreads de mercado por tipo (bps acima do CDI/IPCA) ──────────────────────
SPREADS_MERCADO = {
    "CDB_GRANDE":     {"min": 0,    "max": 30,   "referencia": "CDI"},
    "CDB_MEDIO":      {"min": 50,   "max": 200,  "referencia": "CDI"},
    "LCI_GRANDE":     {"min": -20,  "max": 20,   "referencia": "CDI"},  # isento IR
    "LCA_GRANDE":     {"min": -20,  "max": 20,   "referencia": "CDI"},  # isento IR
    "CRI":            {"min": 50,   "max": 300,  "referencia": "IPCA"},
    "CRA":            {"min": 50,   "max": 300,  "referencia": "IPCA"},
    "DEBENTURE_IG":   {"min": 100,  "max": 300,  "referencia": "CDI"},
    "DEBENTURE_HY":   {"min": 300,  "max": 800,  "referencia": "CDI"},
    "FIDC_SR":        {"min": 100,  "max": 400,  "referencia": "CDI"},
}


def classificar_ativo_rf(ticker: str, classe: str) -> Dict:
    """
    Classifica o ativo de renda fixa e retorna metadados

    Args:
        ticker: Identificador do ativo (ex: TESOURO_IPCA_2035, CDB_ITAU)
        classe: Classe do parser_b3 (TESOURO_IPCA, RF_CDB, etc.)

    Returns:
        Dict com {tipo, subtipo, emissor, fgc_coberto, isento_ir}
    """
    ticker_upper = ticker.upper()
    classe_upper = classe.upper()

    resultado = {
        "tipo": "DESCONHECIDO",
        "emissor": None,
        "fgc_coberto": False,
        "isento_ir": False,
        "garantia_real": False,
    }

    if "TESOURO" in classe_upper or "TESOURO" in ticker_upper:
        resultado.update({
            "tipo": "TESOURO_DIRETO",
            "emissor": "TESOURO",
            "fgc_coberto": False,
            "isento_ir": False,
            "risco_credito": "Soberano",
        })
        if "IPCA" in ticker_upper:
            resultado["subtipo"] = "IPCA+"
            resultado["indexador"] = "IPCA"
        elif "SELIC" in ticker_upper or "RENDA+" in ticker_upper:
            resultado["subtipo"] = "Selic"
            resultado["indexador"] = "SELIC"
        else:
            resultado["subtipo"] = "Prefixado"
            resultado["indexador"] = "PRE"

    elif "CDB" in classe_upper or "CDB" in ticker_upper:
        resultado.update({
            "tipo": "CDB",
            "fgc_coberto": True,
            "isento_ir": False,
            "indexador": "CDI",
        })
        emissor = _extrair_emissor(ticker_upper)
        resultado["emissor"] = emissor

    elif "LCI" in classe_upper or "LCI" in ticker_upper:
        resultado.update({
            "tipo": "LCI",
            "fgc_coberto": True,
            "isento_ir": True,
            "indexador": "CDI",
            "garantia_real": True,
        })
        resultado["emissor"] = _extrair_emissor(ticker_upper)

    elif "LCA" in classe_upper or "LCA" in ticker_upper:
        resultado.update({
            "tipo": "LCA",
            "fgc_coberto": True,
            "isento_ir": True,
            "indexador": "CDI",
        })
        resultado["emissor"] = _extrair_emissor(ticker_upper)

    elif "CRI" in classe_upper or "CRI" in ticker_upper:
        resultado.update({
            "tipo": "CRI",
            "fgc_coberto": False,
            "isento_ir": True,
            "indexador": "IPCA",
            "garantia_real": True,
        })

    elif "CRA" in classe_upper or "CRA" in ticker_upper:
        resultado.update({
            "tipo": "CRA",
            "fgc_coberto": False,
            "isento_ir": True,
            "indexador": "IPCA",
        })

    elif "DEBENTURE" in classe_upper or "DEB" in ticker_upper:
        resultado.update({
            "tipo": "DEBENTURE",
            "fgc_coberto": False,
            "isento_ir": False,
            "indexador": "CDI",
        })

    elif "FIDC" in classe_upper or "FIDC" in ticker_upper:
        resultado.update({
            "tipo": "FIDC",
            "fgc_coberto": False,
            "isento_ir": False,
            "indexador": "CDI",
        })

    return resultado


def _extrair_emissor(ticker: str) -> Optional[str]:
    """Tenta extrair nome do emissor a partir do ticker"""
    for banco in RATINGS_EMISSORES:
        if banco in ticker:
            return banco
    return None


def calcular_duration_estimada(
    vencimento_anos: Optional[float],
    indexador: str,
    taxa_cupom: Optional[float] = None
) -> Optional[Dict]:
    """
    Calcula duration estimada (Macaulay simplificada)

    Para zero-cupom: duration = vencimento
    Para títulos com cupom: duration < vencimento

    Args:
        vencimento_anos: Anos até o vencimento
        indexador: CDI, IPCA, PRE
        taxa_cupom: Taxa de cupom anual (%)

    Returns:
        Dict com {duration_anos, sensibilidade_1pp, classificacao}
    """
    if vencimento_anos is None:
        return None

    # Títulos atrelados ao CDI têm duration próxima de zero (repricing diário)
    if indexador == "CDI":
        duration = min(0.5, vencimento_anos * 0.1)
        sensibilidade = duration * 0.01 * 100  # % do principal para variação de 1pp
        classificacao = "CURTÍSSIMA"
    elif taxa_cupom and taxa_cupom > 0:
        # Duration aproximada com cupom
        taxa_dec = taxa_cupom / 100
        duration = vencimento_anos * (1 - taxa_dec / (1 + taxa_dec)) + 1 / (1 + taxa_dec)
        duration = min(duration, vencimento_anos)
        sensibilidade = duration * 0.01 * 100
        if duration < 1:
            classificacao = "CURTA"
        elif duration < 3:
            classificacao = "MÉDIA"
        elif duration < 7:
            classificacao = "LONGA"
        else:
            classificacao = "MUITO LONGA"
    else:
        # Zero cupom — duration = vencimento
        duration = vencimento_anos
        sensibilidade = duration * 0.01 * 100
        if duration < 1:
            classificacao = "CURTA"
        elif duration < 3:
            classificacao = "MÉDIA"
        elif duration < 7:
            classificacao = "LONGA"
        else:
            classificacao = "MUITO LONGA"

    return {
        "duration_anos": round(duration, 2),
        "sensibilidade_1pp": round(sensibilidade, 2),
        "classificacao": classificacao,
        "nota": f"Variação de 1pp na taxa → {sensibilidade:.2f}% no preço do título",
    }


def calcular_spread_sobre_benchmark(
    taxa_contratada: float,
    benchmark: float,
    tipo: str,
    vencimento_anos: Optional[float] = None
) -> Dict:
    """
    Calcula spread do ativo sobre o benchmark (CDI ou IPCA)

    Args:
        taxa_contratada: Taxa total do ativo (% a.a.)
        benchmark: Taxa do benchmark (CDI ou IPCA atual)
        tipo: Tipo do ativo (CDB, CRI, etc.)
        vencimento_anos: Para contexto de curva

    Returns:
        Dict com {spread_bps, spread_pct, classificacao, vs_mercado}
    """
    spread_pp = taxa_contratada - benchmark
    spread_bps = spread_pp * 100

    # Classificação absoluta
    if spread_bps > 200:
        classificacao = "MUITO ALTO"
        interpretacao = "Alto risco de crédito ou oportunidade"
    elif spread_bps > 100:
        classificacao = "ALTO"
        interpretacao = "Prêmio relevante, verificar risco"
    elif spread_bps > 50:
        classificacao = "MODERADO"
        interpretacao = "Spread saudável para o risco assumido"
    elif spread_bps > 0:
        classificacao = "BAIXO"
        interpretacao = "Spread pequeno — risco de crédito baixo"
    else:
        classificacao = "ABAIXO DO BENCHMARK"
        interpretacao = "Taxa abaixo do benchmark — pouco atrativo"

    # Comparação com mercado
    tipo_upper = tipo.upper()
    vs_mercado = None
    for chave, ref in SPREADS_MERCADO.items():
        if tipo_upper in chave:
            mercado_medio = (ref["min"] + ref["max"]) / 2
            if spread_bps > mercado_medio:
                vs_mercado = "ACIMA DA MÉDIA"
            elif spread_bps >= ref["min"]:
                vs_mercado = "NA MÉDIA"
            else:
                vs_mercado = "ABAIXO DA MÉDIA"
            break

    return {
        "spread_bps": round(spread_bps, 0),
        "spread_pp": round(spread_pp, 2),
        "classificacao": classificacao,
        "interpretacao": interpretacao,
        "vs_mercado": vs_mercado,
    }


def buscar_rating_emissor(emissor: Optional[str]) -> Dict:
    """
    Retorna rating de crédito do emissor

    Args:
        emissor: Nome do emissor (ex: ITAU, BRADESCO)

    Returns:
        Dict com {rating, perspectiva, tipo, score_risco}
    """
    if not emissor:
        return {"rating": "N/A", "score_risco": 5}

    emissor_upper = emissor.upper()

    if emissor_upper in RATINGS_EMISSORES:
        dados = RATINGS_EMISSORES[emissor_upper]
        rating = dados["rating"]
    else:
        # Heurística por tipo de emissor no nome
        if any(w in emissor_upper for w in ["BANCO", "BANK", "BNK"]):
            dados = {"rating": "A", "perspectiva": "Estável", "tipo": "Banco Desconhecido"}
            rating = "A"
        else:
            dados = {"rating": "BBB", "perspectiva": "Estável", "tipo": "Emissor Desconhecido"}
            rating = "BBB"

    # Score de risco por rating
    score_map = {
        "AAA": 1, "AA+": 1.5, "AA": 2, "AA-": 2.5,
        "A+": 3, "A": 3.5, "A-": 4,
        "BBB+": 5, "BBB": 5.5, "BBB-": 6,
        "BB+": 7, "BB": 7.5, "BB-": 8,
        "B": 9, "C": 10
    }
    score_risco = score_map.get(rating, 5)

    return {**dados, "score_risco": score_risco, "emissor": emissor_upper}


def posicionar_na_curva(
    vencimento_anos: Optional[float],
    taxa_contratada: Optional[float],
    indexador: str,
) -> Optional[Dict]:
    """
    Posiciona o ativo na curva de juros atual

    Compara taxa contratada com taxa de mercado para o mesmo vencimento

    Args:
        vencimento_anos: Anos até o vencimento
        taxa_contratada: Taxa do ativo (%)
        indexador: CDI, IPCA, PRE

    Returns:
        Dict com {ponto_curva, taxa_mercado, premio_sobre_curva, avaliacao}
    """
    if vencimento_anos is None or taxa_contratada is None:
        return None

    # Encontrar ponto mais próximo na curva de referência
    pontos = {"1m": 1/12, "3m": 3/12, "6m": 6/12, "1a": 1, "2a": 2, "3a": 3, "5a": 5, "10a": 10}
    mais_proximo = min(pontos, key=lambda k: abs(pontos[k] - vencimento_anos))
    taxa_curva = CURVA_DI_REFERENCIA[mais_proximo]

    # Para IPCA, ajustar benchmark (curva DI - IPCA esperado ~5%)
    if indexador == "IPCA":
        taxa_mercado_comparavel = taxa_curva - 5.0  # spread real esperado
    else:
        taxa_mercado_comparavel = taxa_curva

    premio = taxa_contratada - taxa_mercado_comparavel

    if premio > 1.0:
        avaliacao = "ACIMA DA CURVA"
        emoji = "✅"
    elif premio > -0.5:
        avaliacao = "NA CURVA"
        emoji = "➡️"
    else:
        avaliacao = "ABAIXO DA CURVA"
        emoji = "⚠️"

    return {
        "ponto_curva": mais_proximo,
        "taxa_mercado_referencia": taxa_mercado_comparavel,
        "taxa_contratada": taxa_contratada,
        "premio_sobre_curva_pp": round(premio, 2),
        "avaliacao": avaliacao,
        "emoji": emoji,
    }


def analisar_rf_completo(
    ticker: str,
    classe: str,
    taxa_contratada: Optional[float] = None,
    vencimento_anos: Optional[float] = None,
    valor_investido: Optional[float] = None,
    macro_dados: Optional[Dict] = None,
) -> Dict:
    """
    Análise completa de um ativo de renda fixa

    Orquestra: classificação, duration, spread, rating, posição na curva

    Args:
        ticker: Identificador do ativo
        classe: Classe do ativo (TESOURO_IPCA, RF_CDB, etc.)
        taxa_contratada: Taxa % a.a. (se disponível)
        vencimento_anos: Anos até o vencimento (se disponível)
        valor_investido: Valor em R$ aplicado
        macro_dados: Dict com selic, ipca_12m, cdi

    Returns:
        Dict completo com todos os dados e análise textual
    """
    if macro_dados is None:
        macro_dados = {}

    cdi = macro_dados.get("cdi", 14.35)
    ipca = macro_dados.get("ipca_12m", 5.5)
    selic = macro_dados.get("selic", 14.4)

    resultado = {
        "ticker": ticker,
        "classe": classe,
        "timestamp": datetime.now().isoformat(),
        "dados": {},
    }

    # 1. Classificação
    classif = classificar_ativo_rf(ticker, classe)
    resultado["dados"]["classificacao"] = classif
    indexador = classif.get("indexador", "CDI")

    # Definir benchmark
    benchmark = ipca if indexador == "IPCA" else cdi
    benchmark_nome = "IPCA" if indexador == "IPCA" else "CDI"

    # 2. Estimativa de taxa contratada (fallback)
    if taxa_contratada is None:
        taxa_contratada = _estimar_taxa(classif["tipo"], benchmark)
    resultado["dados"]["taxa_contratada"] = taxa_contratada
    resultado["dados"]["benchmark_nome"] = benchmark_nome
    resultado["dados"]["benchmark_valor"] = benchmark

    # 3. Duration
    if vencimento_anos or _vencimento_por_classe(classif["tipo"]):
        vcto = vencimento_anos or _vencimento_por_classe(classif["tipo"])
        duration = calcular_duration_estimada(vcto, indexador)
        if duration:
            resultado["dados"]["duration"] = duration
            resultado["dados"]["vencimento_anos"] = vcto

    # 4. Spread sobre benchmark
    spread = calcular_spread_sobre_benchmark(taxa_contratada, benchmark, classif["tipo"])
    resultado["dados"]["spread"] = spread

    # 5. Rating do emissor
    rating = buscar_rating_emissor(classif.get("emissor"))
    resultado["dados"]["rating"] = rating

    # 6. Posição na curva
    posicao = posicionar_na_curva(
        resultado["dados"].get("vencimento_anos"),
        taxa_contratada,
        indexador,
    )
    if posicao:
        resultado["dados"]["posicao_curva"] = posicao

    # 7. Taxa real (para prefixados e IPCA+)
    if indexador == "IPCA" and taxa_contratada:
        taxa_real = taxa_contratada  # IPCA+ já é taxa real
        resultado["dados"]["taxa_real"] = taxa_real
    elif indexador == "PRE" and taxa_contratada:
        taxa_real = ((1 + taxa_contratada / 100) / (1 + ipca / 100) - 1) * 100
        resultado["dados"]["taxa_real"] = round(taxa_real, 2)

    # 8. Análise textual
    resultado["analise"] = gerar_analise_rf(resultado["dados"], selic, ipca, cdi)

    return resultado


def _estimar_taxa(tipo: str, benchmark: float) -> float:
    """Estima taxa típica para o tipo, baseada no benchmark atual"""
    tipo_upper = tipo.upper()
    spreads_tipicos = {
        "TESOURO_DIRETO": 0,
        "CDB": 0.5,
        "LCI": 0.3,
        "LCA": 0.3,
        "CRI": 2.0,
        "CRA": 2.0,
        "DEBENTURE": 2.5,
        "FIDC": 3.0,
    }
    for chave, spread in spreads_tipicos.items():
        if chave in tipo_upper:
            return round(benchmark + spread, 2)
    return benchmark


def _vencimento_por_classe(tipo: str) -> Optional[float]:
    """Vencimentos típicos por classe (fallback)"""
    vencimentos = {
        "TESOURO_DIRETO": 5.0,
        "CDB": 1.5,
        "LCI": 1.0,
        "LCA": 1.0,
        "CRI": 4.0,
        "CRA": 3.5,
        "DEBENTURE": 5.0,
        "FIDC": 2.0,
    }
    tipo_upper = tipo.upper()
    for chave, vcto in vencimentos.items():
        if chave in tipo_upper:
            return vcto
    return None


def gerar_analise_rf(
    dados: Dict,
    selic: float,
    ipca: float,
    cdi: float,
) -> str:
    """Gera análise textual interpretativa do ativo de renda fixa"""
    linhas = []

    classif = dados.get("classificacao", {})
    tipo = classif.get("tipo", "N/A")
    indexador = classif.get("indexador", "CDI")
    fgc = classif.get("fgc_coberto", False)
    isento = classif.get("isento_ir", False)

    # Linha 1: tipo + proteções
    protecoes = []
    if fgc:
        protecoes.append("✅ FGC (até R$ 250k)")
    if isento:
        protecoes.append("✅ Isento de IR")
    if classif.get("garantia_real"):
        protecoes.append("✅ Garantia real")
    prot_str = " | ".join(protecoes) if protecoes else "⚠️ Sem FGC"
    linhas.append(f"**Tipo:** {tipo} — {prot_str}")

    # Rating
    rating = dados.get("rating", {})
    if rating.get("rating") and rating["rating"] != "N/A":
        r = rating["rating"]
        persp = rating.get("perspectiva", "")
        tipo_emissor = rating.get("tipo", "")
        linhas.append(f"**Rating:** {r} ({tipo_emissor}) — perspectiva {persp}")

    # Taxa e benchmark
    taxa = dados.get("taxa_contratada")
    bm_nome = dados.get("benchmark_nome", "CDI")
    bm_valor = dados.get("benchmark_valor", cdi)
    if taxa:
        taxa_real = dados.get("taxa_real")
        taxa_real_str = f" | Taxa real: {taxa_real:.2f}% a.a." if taxa_real else ""
        linhas.append(
            f"**Taxa:** {taxa:.2f}% a.a. ({bm_nome} {bm_valor:.2f}%){taxa_real_str}"
        )

    # Spread
    spread = dados.get("spread", {})
    if spread.get("spread_bps") is not None:
        s_bps = spread["spread_bps"]
        s_classif = spread["classificacao"]
        vs_merc = spread.get("vs_mercado", "")
        vs_str = f" — {vs_merc}" if vs_merc else ""
        linhas.append(
            f"**Spread:** {s_bps:+.0f}bps sobre {bm_nome} ({s_classif}{vs_str})"
        )

    # Duration
    dur = dados.get("duration", {})
    if dur.get("duration_anos"):
        d_anos = dur["duration_anos"]
        d_classif = dur["classificacao"]
        sens = dur["sensibilidade_1pp"]
        linhas.append(
            f"**Duration:** {d_anos:.1f} anos ({d_classif}) — "
            f"variação de 1pp na taxa → {sens:.1f}% no preço"
        )

    # Posição na curva
    pos = dados.get("posicao_curva", {})
    if pos.get("avaliacao"):
        emoji = pos.get("emoji", "")
        aval = pos["avaliacao"]
        premio = pos["premio_sobre_curva_pp"]
        ponto = pos["ponto_curva"]
        linhas.append(
            f"**Curva:** {emoji} {aval} — {premio:+.2f}pp vs mercado ({ponto})"
        )

    # Contexto Selic
    if taxa:
        taxa_vs_selic = taxa - selic if indexador != "IPCA" else taxa + ipca - selic
        if taxa_vs_selic > 0:
            linhas.append(
                f"**vs Selic:** Retorno bruto {taxa_vs_selic:+.2f}pp acima da Selic"
            )
        else:
            linhas.append(
                f"**vs Selic:** ⚠️ Retorno {taxa_vs_selic:.2f}pp abaixo da Selic"
            )

    return "\n".join(linhas) if linhas else "Dados insuficientes para análise"


if __name__ == "__main__":
    print("Testando análise de renda fixa...\n")

    macro = {"cdi": 14.35, "ipca_12m": 5.5, "selic": 14.4}

    testes = [
        ("TESOURO_IPCA_2035", "TESOURO_IPCA", 7.5, 9.0),
        ("TESOURO_SELIC_2027", "TESOURO_SELIC", 14.4, 1.5),
        ("CDB_ITAU_CDI_120", "RF_CDB", 120 * 14.35 / 100, 2.0),
        ("LCI_BRADESCO_98CDI", "RF_LCI", 98 * 14.35 / 100, 1.0),
        ("CRI_SETOR_IPCA_PLUS_5", "RF_CRI", 5.0, 4.0),
    ]

    for ticker, classe, taxa, vcto in testes:
        r = analisar_rf_completo(ticker, classe, taxa, vcto, macro_dados=macro)
        print(f"📊 {ticker}")
        print(r["analise"])
        print("---\n")
