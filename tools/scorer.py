"""
Scorer de Ativos — Pontua e classifica ativos em uma escala 0-10
"""

from typing import Dict, Any, Optional
from tools.calculadores import CalculadoresEspecializados


class ScorerAtivos:
    """Gera scores de qualidade para ativos"""

    @staticmethod
    def gerar_score_acao(dados_yf: Dict[str, Any], macro_dados: Dict[str, float]) -> Dict[str, Any]:
        """
        Gera score para ação brasileira
        Usa: P/L, P/VP, DY, setor, beta
        """
        if not dados_yf:
            return {"score": "N/A", "categoria": "Sem dados"}

        p_l = dados_yf.get("p_l")
        p_vp = dados_yf.get("p_vp")
        dy = dados_yf.get("dividend_yield", 0)
        beta = dados_yf.get("beta")

        # Scoring simplificado sem ROIC/ROE (que não temos via yfinance)
        score_dict = CalculadoresEspecializados.calcular_score_acao(
            pl=p_l,
            pvp=p_vp,
            crescimento_lpa=None  # Não temos esse dado
        )

        score = score_dict.get("score", 5)

        # Ajustar por DY
        if dy and dy > 0.08:  # > 8% é bom para ação
            score = min(score + 1, 10)

        # Ajustar por beta (beta alto = risco)
        if beta:
            if beta < 0.8:
                score = min(score + 0.5, 10)
            elif beta > 1.3:
                score = max(score - 0.5, 1)

        # Classificação de risco
        if score >= 8:
            categoria = "Excelente"
        elif score >= 7:
            categoria = "Bom"
        elif score >= 5:
            categoria = "Neutro"
        elif score >= 3:
            categoria = "Fraco"
        else:
            categoria = "Crítico"

        return {
            "score": round(score, 1),
            "categoria": categoria,
            "P/L": p_l,
            "P/VP": p_vp,
            "DY": f"{dy*100:.2f}%" if dy else "N/A",
            "Beta": f"{beta:.2f}" if beta else "N/A"
        }

    @staticmethod
    def gerar_score_fii(dados_yf: Dict[str, Any], macro_dados: Dict[str, float]) -> Dict[str, Any]:
        """
        Gera score para FII
        Usa: DY, liquidez, cotação vs histórico
        """
        if not dados_yf:
            return {"score": "N/A", "categoria": "Sem dados"}

        dy_12m = dados_yf.get("dividend_yield_12m", 0)
        selic = macro_dados.get("selic", 13.75)

        # Comparar DY com Selic
        score = 5  # Neutro por padrão

        # Se DY > Selic * 1.1, é interessante
        if dy_12m > selic * 1.1:
            score = 7  # Bom
            if dy_12m > selic * 1.2:
                score = 8  # Muito bom

        # Se DY < Selic * 0.9, é fraco
        elif dy_12m < selic * 0.9:
            score = 3  # Fraco

        # Classificação
        if score >= 8:
            categoria = "Muito Atrativo"
        elif score >= 7:
            categoria = "Atrativo"
        elif score >= 5:
            categoria = "Neutro"
        else:
            categoria = "Pouco Atrativo"

        return {
            "score": round(score, 1),
            "categoria": categoria,
            "DY 12m": f"{dy_12m:.2f}%",
            "Selic": f"{selic:.2f}%",
            "Diferencial": f"{dy_12m - selic:.2f}pp"
        }

    @staticmethod
    def gerar_score_tesouro(tipo: str, macro_dados: Dict[str, float], valor: float = 0) -> Dict[str, Any]:
        """
        Gera score para Tesouro Direto
        """
        selic = macro_dados.get("selic", 13.75)
        ipca_12m = macro_dados.get("ipca_12m", 4.83)
        taxa_real = selic - ipca_12m

        if "IPCA" in tipo:
            # Taxa real > 6% é excelente para IPCA+
            if taxa_real > 6:
                score = 9
                categoria = "Excelente"
            elif taxa_real > 4:
                score = 7
                categoria = "Bom"
            else:
                score = 5
                categoria = "Neutro"

            return {
                "score": round(score, 1),
                "categoria": categoria,
                "Taxa Real": f"{taxa_real:.2f}%",
                "Tipo": "Tesouro IPCA+",
                "Objetivo": "Proteção contra inflação"
            }

        elif "SELIC" in tipo or "Renda+" in tipo:
            # Selic alta é bom para Selic
            if selic > 12:
                score = 8
                categoria = "Atrativo"
            elif selic > 10:
                score = 7
                categoria = "Bom"
            else:
                score = 5
                categoria = "Neutro"

            return {
                "score": round(score, 1),
                "categoria": categoria,
                "Selic": f"{selic:.2f}%",
                "Tipo": tipo,
                "Objetivo": "Liquidez e segurança"
            }

        else:
            # Prefixado
            return {
                "score": 6.0,
                "categoria": "Bom",
                "Tipo": "Tesouro Prefixado",
                "Objetivo": "Travamento de taxa"
            }

    @staticmethod
    def gerar_score_cdb(taxa_contratada: Optional[float], cdi: float) -> Dict[str, Any]:
        """
        Gera score para CDB
        """
        if not taxa_contratada:
            taxa_contratada = cdi * 0.95  # Estimativa

        spread = taxa_contratada - cdi

        if spread > 1.0:  # > 100bps
            score = 8
            categoria = "Atrativo"
        elif spread > 0:
            score = 6
            categoria = "Razoável"
        else:
            score = 3
            categoria = "Pouco Atrativo"

        return {
            "score": round(score, 1),
            "categoria": categoria,
            "Taxa": f"{taxa_contratada:.2f}%",
            "CDI": f"{cdi:.2f}%",
            "Spread": f"{spread:.2f}pp"
        }

    @staticmethod
    def gerar_score_etf(dados_yf: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera score para ETF
        """
        if not dados_yf:
            return {"score": 5.0, "categoria": "Neutro"}

        # ETF é mais sobre liquidez e TER
        aum = dados_yf.get("aum", 0)
        performance_1y = dados_yf.get("performance_1y", 0)

        # AUM > 100M é bom
        if aum and aum > 100_000_000:
            score = 7
        else:
            score = 5

        return {
            "score": round(score, 1),
            "categoria": "Bom",
            "AUM": f"R$ {aum/1e6:.1f}M" if aum else "N/A",
            "Performance 1y": f"{performance_1y:.2f}%",
            "Objetivo": "Diversificação"
        }

    @staticmethod
    def gerar_score_generico(classe: str, dados_yf: Dict[str, Any], macro_dados: Dict[str, float]) -> Dict[str, Any]:
        """
        Score genérico para classes não categorizadas
        """
        return {
            "score": 5.0,
            "categoria": "Neutro",
            "classe": classe,
            "status": "Sem score específico disponível"
        }


def calcular_score_por_classe(
    classe: str,
    ticker: str,
    dados_yf: Dict[str, Any],
    macro_dados: Dict[str, float],
    valor_total: float = 0
) -> Dict[str, Any]:
    """
    Interface unificada para calcular score de qualquer ativo
    """
    scorer = ScorerAtivos()

    resultado = {
        "ticker": ticker,
        "classe": classe,
        "score": 5.0,
        "categoria": "Neutro",
        "detalhes": {}
    }

    try:
        if classe == "ACAO_BR":
            resultado.update(scorer.gerar_score_acao(dados_yf, macro_dados))

        elif classe == "FII":
            resultado.update(scorer.gerar_score_fii(dados_yf, macro_dados))

        elif "TESOURO" in classe:
            resultado.update(scorer.gerar_score_tesouro(classe, macro_dados, valor_total))

        elif classe == "RENDA_FIXA_PRIVADA":
            cdi = macro_dados.get("cdi", 13.65)
            resultado.update(scorer.gerar_score_cdb(None, cdi))

        elif classe == "ETF_BR":
            resultado.update(scorer.gerar_score_etf(dados_yf))

        else:
            resultado.update(scorer.gerar_score_generico(classe, dados_yf, macro_dados))

    except Exception as e:
        resultado["erro"] = str(e)

    return resultado


if __name__ == "__main__":
    # Teste
    macro = {
        "selic": 13.75,
        "ipca_12m": 4.83,
        "cdi": 13.65
    }

    dados_acao = {"p_l": 8.5, "p_vp": 1.2, "dividend_yield": 0.05, "beta": 0.9}
    resultado = calcular_score_por_classe("ACAO_BR", "PETR4", dados_acao, macro)
    print(f"PETR4: {resultado}")

    dados_fii = {"dividend_yield_12m": 11.96}
    resultado = calcular_score_por_classe("FII", "MXRF11", dados_fii, macro)
    print(f"MXRF11: {resultado}")
