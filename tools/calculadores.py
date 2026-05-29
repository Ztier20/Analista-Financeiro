"""
Calculadores de Indicadores Financeiros
ROE, ROIC, margens, FCF, Dívida/EBITDA, Sharpe
"""

from typing import Dict, Optional


class CalculadoresFinanceiros:
    """Calcula indicadores fundamentalistas a partir de dados de demonstrações"""

    @staticmethod
    def calcular_roe(lucro_liquido: float, patrimonio_liquido: float) -> Optional[float]:
        """ROE = Lucro Líquido / Patrimônio Líquido"""
        if patrimonio_liquido <= 0:
            return None
        return (lucro_liquido / patrimonio_liquido) * 100

    @staticmethod
    def calcular_roic(nopat: float, capital_investido: float) -> Optional[float]:
        """ROIC = NOPAT / Capital Investido
        NOPAT = EBIT * (1 - Alíquota de Imposto)
        """
        if capital_investido <= 0:
            return None
        return (nopat / capital_investido) * 100

    @staticmethod
    def calcular_margem_bruta(receita: float, cogs: float) -> Optional[float]:
        """Margem Bruta = (Receita - COGS) / Receita"""
        if receita <= 0:
            return None
        return ((receita - cogs) / receita) * 100

    @staticmethod
    def calcular_margem_ebitda(ebitda: float, receita: float) -> Optional[float]:
        """Margem EBITDA = EBITDA / Receita"""
        if receita <= 0:
            return None
        return (ebitda / receita) * 100

    @staticmethod
    def calcular_margem_liquida(lucro_liquido: float, receita: float) -> Optional[float]:
        """Margem Líquida = Lucro Líquido / Receita"""
        if receita <= 0:
            return None
        return (lucro_liquido / receita) * 100

    @staticmethod
    def calcular_divida_ebitda(divida_liquida: float, ebitda: float) -> Optional[float]:
        """Dívida/EBITDA = Dívida Líquida / EBITDA"""
        if ebitda <= 0:
            return None
        return divida_liquida / ebitda

    @staticmethod
    def calcular_cobertura_juros(ebit: float, despesas_financeiras: float) -> Optional[float]:
        """Cobertura de Juros = EBIT / Despesas Financeiras"""
        if despesas_financeiras <= 0:
            return None
        return ebit / despesas_financeiras

    @staticmethod
    def calcular_fcf(fluxo_operacional: float, capex: float) -> float:
        """FCF = Fluxo de Caixa Operacional - CapEx"""
        return fluxo_operacional - capex

    @staticmethod
    def calcular_cagr(valor_inicial: float, valor_final: float, anos: int) -> Optional[float]:
        """CAGR = (Valor Final / Valor Inicial)^(1/anos) - 1"""
        if valor_inicial <= 0 or anos <= 0:
            return None
        return ((valor_final / valor_inicial) ** (1 / anos) - 1) * 100

    @staticmethod
    def calcular_payout_ratio(dividendos: float, lucro_liquido: float) -> Optional[float]:
        """Payout Ratio = Dividendos / Lucro Líquido"""
        if lucro_liquido <= 0:
            return None
        return (dividendos / lucro_liquido) * 100

    @staticmethod
    def calcular_sharpe(retorno_anual: float, desvio_padrao: float, taxa_livre_risco: float = 13.75) -> Optional[float]:
        """Índice de Sharpe = (Retorno - Taxa Livre de Risco) / Desvio Padrão"""
        if desvio_padrao <= 0:
            return None
        return (retorno_anual - taxa_livre_risco) / desvio_padrao


class CalculadoresEspecializados:
    """Calculadores para classes específicas de ativos"""

    @staticmethod
    def calcular_score_acao(
        roe: Optional[float] = None,
        roic: Optional[float] = None,
        margem_liquida: Optional[float] = None,
        divida_ebitda: Optional[float] = None,
        pl: Optional[float] = None,
        pvp: Optional[float] = None,
        crescimento_lpa: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Score para ação (0-10)
        Pesos: ROE (20%) | ROIC (15%) | Margens (15%) | Saúde Financeira (20%) | Valuation (20%) | Crescimento (10%)
        """
        scores = {}
        pesos_totais = 0

        # ROE: > 15% = excelente, 10-15% = bom, < 10% = fraco
        if roe is not None:
            if roe > 15:
                scores["roe"] = (8, 0.20)
            elif roe > 10:
                scores["roe"] = (6, 0.20)
            else:
                scores["roe"] = (3, 0.20)
            pesos_totais += 0.20

        # ROIC: > 12% = excelente, 8-12% = bom, < 8% = fraco
        if roic is not None:
            if roic > 12:
                scores["roic"] = (8, 0.15)
            elif roic > 8:
                scores["roic"] = (6, 0.15)
            else:
                scores["roic"] = (3, 0.15)
            pesos_totais += 0.15

        # Margem Líquida: > 10% = excelente, 5-10% = bom, < 5% = fraco
        if margem_liquida is not None:
            if margem_liquida > 10:
                scores["margem"] = (8, 0.15)
            elif margem_liquida > 5:
                scores["margem"] = (6, 0.15)
            else:
                scores["margem"] = (3, 0.15)
            pesos_totais += 0.15

        # Dívida/EBITDA: < 2x = excelente, 2-3x = bom, > 3x = fraco
        if divida_ebitda is not None:
            if divida_ebitda < 2:
                scores["divida"] = (8, 0.20)
            elif divida_ebitda < 3:
                scores["divida"] = (6, 0.20)
            else:
                scores["divida"] = (3, 0.20)
            pesos_totais += 0.20

        # Valuation P/L: < setor médio (15) = bom, > setor = caro
        # P/VP: < 1.5 = bom, > 2 = caro
        if pl is not None or pvp is not None:
            valuation_score = 5  # neutro por padrão

            if pl and pl < 12:
                valuation_score = 8
            elif pl and pl > 18:
                valuation_score = 3
            elif pvp and pvp < 1.2:
                valuation_score = 8
            elif pvp and pvp > 2:
                valuation_score = 3

            scores["valuation"] = (valuation_score, 0.20)
            pesos_totais += 0.20

        # Crescimento LPA: > 10% CAGR = bom, 5-10% = neutro, < 5% = fraco
        if crescimento_lpa is not None:
            if crescimento_lpa > 10:
                scores["crescimento"] = (8, 0.10)
            elif crescimento_lpa > 5:
                scores["crescimento"] = (6, 0.10)
            else:
                scores["crescimento"] = (3, 0.10)
            pesos_totais += 0.10

        # Calcular score ponderado
        if not scores:
            return {"score": 5, "componentes": {}}

        score_total = sum(score * peso for score, peso in scores.values())
        if pesos_totais > 0:
            score_total = score_total / pesos_totais

        return {
            "score": round(score_total, 2),
            "componentes": {k: v[0] for k, v in scores.items()},
            "pesos_usados": pesos_totais
        }

    @staticmethod
    def calcular_score_fii(
        p_vp: Optional[float] = None,
        dy_12m: Optional[float] = None,
        vacancia: Optional[float] = None,
        inadimplencia: Optional[float] = None,
        alavancagem: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Score para FII (0-10)
        Pesos: P/VP (25%) | DY (25%) | Vacância (20%) | Inadimplência (15%) | Alavancagem (15%)
        """
        scores = {}
        pesos_totais = 0

        # P/VP: < 0.85 = excelente, 0.85-1.15 = bom, > 1.15 = caro
        if p_vp is not None:
            if p_vp < 0.85:
                scores["p_vp"] = (9, 0.25)
            elif p_vp < 1.15:
                scores["p_vp"] = (7, 0.25)
            else:
                scores["p_vp"] = (4, 0.25)
            pesos_totais += 0.25

        # DY 12m: > 10% = excelente, 7-10% = bom, < 7% = fraco
        if dy_12m is not None:
            if dy_12m > 10:
                scores["dy"] = (9, 0.25)
            elif dy_12m > 7:
                scores["dy"] = (7, 0.25)
            else:
                scores["dy"] = (4, 0.25)
            pesos_totais += 0.25

        # Vacância: < 5% = excelente, 5-15% = bom, > 15% = fraco
        if vacancia is not None:
            if vacancia < 5:
                scores["vacancia"] = (9, 0.20)
            elif vacancia < 15:
                scores["vacancia"] = (7, 0.20)
            else:
                scores["vacancia"] = (3, 0.20)
            pesos_totais += 0.20

        # Inadimplência: < 1% = excelente, 1-3% = bom, > 3% = preocupante
        if inadimplencia is not None:
            if inadimplencia < 1:
                scores["inadimplencia"] = (9, 0.15)
            elif inadimplencia < 3:
                scores["inadimplencia"] = (7, 0.15)
            else:
                scores["inadimplencia"] = (3, 0.15)
            pesos_totais += 0.15

        # Alavancagem (dívida/patrimônio): < 30% = bom, 30-50% = aceitável, > 50% = alto
        if alavancagem is not None:
            if alavancagem < 30:
                scores["alavancagem"] = (8, 0.15)
            elif alavancagem < 50:
                scores["alavancagem"] = (6, 0.15)
            else:
                scores["alavancagem"] = (3, 0.15)
            pesos_totais += 0.15

        # Calcular score ponderado
        if not scores:
            return {"score": 5, "componentes": {}}

        score_total = sum(score * peso for score, peso in scores.values())
        if pesos_totais > 0:
            score_total = score_total / pesos_totais

        return {
            "score": round(score_total, 2),
            "componentes": {k: v[0] for k, v in scores.items()},
            "pesos_usados": pesos_totais
        }

    @staticmethod
    def calcular_score_renda_fixa(
        dy_anual: Optional[float] = None,
        spread_cdi: Optional[float] = None,
        rating: Optional[str] = None,
        fgc_coberto: bool = True
    ) -> Dict[str, float]:
        """
        Score para renda fixa (0-10)
        Considera: DY vs CDI, spread, rating de crédito, cobertura FGC
        """
        scores = {}
        pesos_totais = 0

        # Rating de crédito
        rating_scores = {
            "AAA": 10,
            "AA": 9,
            "A": 8,
            "BBB": 6,
            "BB": 4,
            "B": 2,
            "C": 1
        }

        if rating and rating.upper() in rating_scores:
            scores["rating"] = (rating_scores[rating.upper()], 0.40)
            pesos_totais += 0.40

        # DY: > 110% do CDI = bom, 90-110% = neutro, < 90% = fraco
        if dy_anual is not None:
            if dy_anual > 11:  # Assumindo CDI ~10%
                scores["dy"] = (8, 0.30)
            elif dy_anual > 9:
                scores["dy"] = (6, 0.30)
            else:
                scores["dy"] = (3, 0.30)
            pesos_totais += 0.30

        # FGC coberto
        if fgc_coberto:
            scores["fgc"] = (8, 0.15)
            pesos_totais += 0.15
        else:
            scores["fgc"] = (4, 0.15)
            pesos_totais += 0.15

        # Spread: < 50bps = excelente, 50-150bps = bom, > 150bps = alto risco
        if spread_cdi is not None:
            if spread_cdi < 50:
                scores["spread"] = (8, 0.15)
            elif spread_cdi < 150:
                scores["spread"] = (6, 0.15)
            else:
                scores["spread"] = (3, 0.15)
            pesos_totais += 0.15

        # Calcular score ponderado
        if not scores:
            return {"score": 5, "componentes": {}}

        score_total = sum(score * peso for score, peso in scores.values())
        if pesos_totais > 0:
            score_total = score_total / pesos_totais

        return {
            "score": round(score_total, 2),
            "componentes": {k: v[0] for k, v in scores.items()},
            "pesos_usados": pesos_totais
        }
