"""
Dados Macroeconômicos — Contexto para análise de carteira
Busca Selic, IPCA, CDI via BCB Open Data (sem autenticação)
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional


class DadosMacro:
    """Busca e cache de dados macroeconômicos"""

    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

    def _buscar_bcb(self, serie_id: int) -> Optional[float]:
        """Busca última taxa de uma série do BCB"""
        try:
            url = f"{self.base_url}.{serie_id}/dados/ultimos/1"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()

            dados = response.json()
            if dados and len(dados) > 0:
                return float(dados[0]["valor"])
            return None

        except Exception as e:
            print(f"⚠️  Erro ao buscar série {serie_id}: {e}")
            return None

    def obter_selic(self) -> float:
        """Taxa Selic média anual (série 11) - convertida de diária para anual"""
        if "selic" not in self.cache:
            valor = self._buscar_bcb(11)
            if valor is not None:
                # Série 11 retorna taxa DIÁRIA, converter para anual (252 dias úteis)
                self.cache["selic"] = ((1 + valor / 100) ** 252 - 1) * 100
            else:
                # Fallback: valores realistas se API falhar
                self.cache["selic"] = 13.75
        return self.cache["selic"]

    def obter_ipca_12m(self) -> float:
        """IPCA últimos 12 meses (série 13522)"""
        if "ipca_12m" not in self.cache:
            valor = self._buscar_bcb(13522)
            self.cache["ipca_12m"] = valor if valor is not None else 4.83
        return self.cache["ipca_12m"]

    def obter_cdi(self) -> float:
        """CDI acumulado anual (série 4189)"""
        if "cdi" not in self.cache:
            valor = self._buscar_bcb(4189)
            # Série 4189 já retorna taxa anual acumulada
            self.cache["cdi"] = valor if valor is not None else 13.65
        return self.cache["cdi"]

    def obter_usdbrl(self) -> float:
        """Cotação USD/BRL via yfinance"""
        if "usdbrl" not in self.cache:
            try:
                import yfinance as yf
                ticker = yf.Ticker("USDBRL=X")
                valor = ticker.info.get("currentPrice")
                self.cache["usdbrl"] = valor if valor is not None else 4.95
            except Exception as e:
                self.cache["usdbrl"] = 4.95  # Fallback

        return self.cache["usdbrl"]

    def obter_todas(self) -> Dict[str, float]:
        """Retorna todos os indicadores macro"""
        return {
            "selic": self.obter_selic(),
            "ipca_12m": self.obter_ipca_12m(),
            "cdi": self.obter_cdi(),
            "usdbrl": self.obter_usdbrl(),
            "timestamp": datetime.now().isoformat()
        }

    def resumo(self) -> str:
        """Retorna resumo formatado"""
        dados = self.obter_todas()
        return f"""
╔════════════════════════════════════════╗
║      CONTEXTO MACROECONÔMICO ATUAL     ║
╠════════════════════════════════════════╣
║ Selic:        {dados["selic"]:>6.2f}% a.a.
║ IPCA 12m:     {dados["ipca_12m"]:>6.2f}% a.a.
║ CDI:          {dados["cdi"]:>6.2f}% a.a.
║ USD/BRL:      R$ {dados["usdbrl"] or 0:>6.2f}
║ Atualizado:   {dados["timestamp"]}
╚════════════════════════════════════════╝
""".strip()


# Instância global
macro = DadosMacro()


if __name__ == "__main__":
    dados = macro.obter_todas()
    print(macro.resumo())
    print(f"\nDados estruturados: {dados}")
