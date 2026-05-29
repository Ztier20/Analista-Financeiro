"""
Interpretador Financeiro — Análise técnica e recomendações
Transforma dados em interpretação e recomendação acionável
"""

from typing import Dict, Any, Tuple, Optional


class Interpretador:
    """Gera análises e recomendações por classe de ativo"""

    def __init__(self, macro_data: Dict[str, float]):
        """
        macro_data: {selic, ipca_12m, cdi, usdbrl}
        """
        self.selic = macro_data.get("selic", 0)
        self.ipca_12m = macro_data.get("ipca_12m", 0)
        self.cdi = macro_data.get("cdi", 0)
        self.usdbrl = macro_data.get("usdbrl", 1)

    def interpretar_fii_papel(
        self,
        ticker: str,
        dados_brapi: Optional[Dict] = None,
        dados_yf: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Interpreta FII de papel (CRIs/LCIs)
        Retorna: (recomendação, análise_textual)
        """
        if not dados_yf:
            return "N/A", "Dados insuficientes"

        dy_12m = dados_yf.get("dividend_yield_12m")
        preco = dados_yf.get("cotacao_atual", 0)
        p_vp = dados_brapi.get("p_vp") if dados_brapi else None

        if not dy_12m or not preco:
            return "N/A", "Dados insuficientes"

        # Lógica de recomendação
        dy_vs_selic = (dy_12m / self.selic) if self.selic > 0 else 0

        analise = f"DY 12m: {dy_12m:.2f}% | Selic: {self.selic:.2f}% | Taxa real: {self.selic - self.ipca_12m:.2f}%"

        if dy_vs_selic > 1.15:
            # DY muito maior que Selic — prêmio de risco interessante
            if p_vp and p_vp < 0.90:
                recomendacao = "AUMENTE"
                motivo = f"DY atrativa ({dy_12m:.1f}%) com P/VP descontado ({p_vp:.2f})"
            elif p_vp and p_vp > 1.10:
                recomendacao = "MANTENHA"
                motivo = f"DY cobre o prêmio de risco mesmo com P/VP elevado ({p_vp:.2f})"
            else:
                recomendacao = "AUMENTE"
                motivo = f"DY significativamente acima de Selic ({dy_12m:.1f}% vs {self.selic:.1f}%)"
        elif dy_vs_selic > 0.95:
            # DY próxima a Selic — depende de P/VP
            if p_vp and p_vp < 0.85:
                recomendacao = "MANTENHA"
                motivo = f"P/VP descontado ({p_vp:.2f}) compensa DY em linha com Selic"
            else:
                recomendacao = "REDUZA"
                motivo = f"Renda fixa paga {self.selic:.1f}% com menos risco"
        else:
            # DY menor que Selic — claramente pior que RF
            recomendacao = "REDUZA"
            motivo = f"DY inferior a Selic em {self.selic - dy_12m:.1f}pp sem compensação"

        return recomendacao, f"{analise} → {motivo}"

    def interpretar_fii_tijolo(
        self,
        ticker: str,
        dados_brapi: Optional[Dict] = None,
        dados_yf: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """Interpreta FII de tijolo (shoppings, galpões, hotéis)"""
        if not dados_yf:
            return "N/A", "Dados insuficientes"

        dy_12m = dados_yf.get("dividend_yield_12m", 0)
        p_vp = dados_brapi.get("p_vp") if dados_brapi else None

        # FIIs de tijolo têm sensibilidade maior a juros
        # Com Selic alta, pressão no cap rate
        selic_elevada = self.selic > 12

        analise = f"DY 12m: {dy_12m:.2f}% | Selic: {self.selic:.2f}%"

        if selic_elevada and dy_12m < self.selic * 1.2:
            recomendacao = "REDUZA"
            motivo = f"Juros altos pressionam valuation; DY {dy_12m:.1f}% não compensa"
        elif p_vp and p_vp < 0.85:
            recomendacao = "MANTENHA"
            motivo = f"P/VP {p_vp:.2f} oferece margem de segurança"
        elif p_vp and p_vp > 1.15:
            recomendacao = "REDUZA"
            motivo = f"Valuation elevado ({p_vp:.2f}) em ambiente de juros altos"
        else:
            recomendacao = "MANTENHA"
            motivo = f"Valuation e DY em equilíbrio"

        return recomendacao, f"{analise} → {motivo}"

    def interpretar_acao_br(
        self,
        ticker: str,
        setor: Optional[str] = None,
        dados_brapi: Optional[Dict] = None,
        dados_yf: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """Interpreta ação brasileira com contexto setorial"""
        if not dados_yf:
            return "N/A", "Dados insuficientes"
        # Nota: brapi é opcional (401 é comum), usa-se apenas yfinance

        p_l = dados_yf.get("p_l")
        p_vp = dados_yf.get("p_vp")
        dy = dados_yf.get("dividend_yield", 0)
        setor = setor or dados_yf.get("setor", "Genérico")

        analise = f"P/L: {p_l or 'N/A'} | P/VP: {p_vp or 'N/A'} | DY: {dy*100 if dy else 0:.2f}%"

        # Lógica simplificada por setor
        if "Financial" in setor or "Bank" in setor:
            # Bancos: juros altos = spread bancário melhor
            if self.selic > 11:
                recomendacao = "AUMENTE" if (p_l and p_l < 8) else "MANTENHA"
                motivo = f"Spread bancário forte com Selic a {self.selic:.1f}%"
            else:
                recomendacao = "MANTENHA"
                motivo = "Rendimento estável em qualquer ciclo"

        elif "Utilities" in setor or "Energy" in setor:
            # Utilities: receita indexada protege, mas taxa de desconto sensível a juros
            if p_l and p_l < 12 and dy > 0.05:
                recomendacao = "MANTENHA"
                motivo = f"Receita protegida + DY {dy*100:.1f}% com P/L razoável"
            else:
                recomendacao = "REDUZA"
                motivo = "Valor justo pressionado pela taxa de desconto elevada"

        elif "Basic" in setor:
            # Commodities: dependem de ciclo externo
            recomendacao = "MANTENHA"
            motivo = "Commodity: mantém para diversificação global"

        else:
            # Genérico: valuation simples
            if p_l and p_l < 10 and (p_vp and p_vp < 1.5):
                recomendacao = "AUMENTE" if dy > 0.03 else "MANTENHA"
                motivo = f"Valuation atrativo: P/L {p_l:.1f} e P/VP {p_vp:.2f}"
            elif p_l and p_l > 15:
                recomendacao = "REDUZA"
                motivo = f"Valuation elevado: P/L {p_l:.1f}"
            else:
                recomendacao = "MANTENHA"
                motivo = "Valuation em linha com mercado"

        return recomendacao, f"{analise} | {setor} → {motivo}"

    def interpretar_tesouro(
        self,
        ticker: str,
        tipo: str = "SELIC",
        valor_total: float = 0
    ) -> Tuple[str, str]:
        """Interpreta Tesouro Direto"""
        taxa_real = self.selic - self.ipca_12m

        if "IPCA" in tipo:
            # Tesouro IPCA+
            if taxa_real > 6:
                recomendacao = "AUMENTE"
                motivo = f"Taxa real {taxa_real:.2f}% excelente para lock-in de longo prazo"
            else:
                recomendacao = "MANTENHA"
                motivo = f"Taxa real {taxa_real:.2f}% protege contra inflação"

            analise = f"Tipo: Tesouro IPCA+ | Taxa real: {taxa_real:.2f}% | IPCA 12m: {self.ipca_12m:.2f}%"

        elif "SELIC" in tipo or "Renda+" in tipo:
            # Tesouro Selic ou Renda+ — proteção contra subida de juros
            if self.selic > 12:
                recomendacao = "MANTENHA"
                motivo = "Flexibilidade em período de incerteza de juros"
            else:
                recomendacao = "CONSIDEREMINVESTIMENTOS_PIMP"
                motivo = "Juros baixos: avaliar Tesouro Prefixado"

            analise = f"Tipo: {tipo} | Selic: {self.selic:.2f}% | Proteção contra subida de juros"

        else:
            # Prefixado
            recomendacao = "MANTENHA"
            motivo = "Travamento de taxa em ambiente incerto"
            analise = f"Tipo: Tesouro Prefixado | Rentabilidade travada"

        return recomendacao, analise + f" → {motivo}"

    def interpretar_cdb(
        self,
        ticker: str,
        taxa_contratada: Optional[float] = None,
        dias_restantes: int = 0
    ) -> Tuple[str, str]:
        """Interpreta CDB"""
        if not taxa_contratada:
            taxa_contratada = self.cdi * 0.95  # Estimativa conservadora

        spread = taxa_contratada - self.cdi

        analise = f"Taxa contratada: {taxa_contratada:.2f}% | CDI: {self.cdi:.2f}% | Spread: {spread:.2f}pp"

        if spread > 0.5:
            recomendacao = "MANTENHA"
            motivo = f"Spread {spread:.2f}pp sobre CDI é atrativo"
        elif spread > -1:
            recomendacao = "MANTENHA"
            motivo = f"Taxa próxima a CDI: resgatar no vencimento e reaplicar"
        else:
            recomendacao = "REDUZA"
            motivo = f"Spread negativo: renda fixa pública paga mais"

        return recomendacao, analise + f" → {motivo}"

    def interpretar_etf(
        self,
        ticker: str,
        dados_yf: Optional[Dict] = None,
        indice: str = "S&P 500"
    ) -> Tuple[str, str]:
        """Interpreta ETF"""
        if not dados_yf:
            return "N/A", "Dados insuficientes"

        performance_1y = dados_yf.get("performance_1y", 0)
        aum = dados_yf.get("aum")

        # Formatar AUM seguro (pode ser None)
        aum_str = f"R$ {aum/1e9:.1f}B" if aum else "N/D"
        analise = f"Performance 1y: {performance_1y:.2f}% | Índice: {indice} | AUM: {aum_str}"

        recomendacao = "MANTENHA"
        motivo = f"ETF de renda variável para diversificação; hold para longo prazo"

        return recomendacao, analise + f" → {motivo}"


if __name__ == "__main__":
    # Teste
    macro = {
        "selic": 13.75,
        "ipca_12m": 4.83,
        "cdi": 13.65,
        "usdbrl": 4.95
    }

    interp = Interpretador(macro)

    # Teste FII papel
    rec, anl = interp.interpretar_fii_papel(
        "MXRF11",
        dados_brapi={"p_vp": 0.92},
        dados_yf={"dividend_yield_12m": 11.96, "cotacao_atual": 9.99}
    )
    print(f"MXRF11: {rec}\n{anl}\n")
