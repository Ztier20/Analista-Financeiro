"""
Cliente Brapi — Dados fundamentalistas de ativos brasileiros
API: https://brapi.dev — sem autenticação necessária
"""

import requests
from typing import Dict, Any, Optional


class BrapiClient:
    """Cliente para API Brapi"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://brapi.dev/api/quote"
        self.cache = {}

    def buscar_ativo(self, ticker: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Busca dados fundamentalistas de um ativo (FII ou Ação)"""
        if ticker in self.cache:
            return self.cache[ticker]

        try:
            # Adicionar .SA para ativos nacionais
            ticker_sa = ticker if ".SA" in ticker else f"{ticker}.SA"

            url = f"{self.base_url}/{ticker_sa}"
            params = {"fundamental": "true"}

            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            dados = response.json()

            # Brapi retorna {results: [...], status: ...}
            if dados.get("status") == 200 and dados.get("results"):
                ativo_data = dados["results"][0]

                resultado = {
                    "ticker": ticker,
                    "preco_atual": ativo_data.get("regularMarketPrice"),
                    "p_l": ativo_data.get("trailingPE"),
                    "p_vp": ativo_data.get("priceToBook"),
                    "dy": ativo_data.get("dividendYield"),
                    "dy_12m": ativo_data.get("dividendYield"),  # Brapi fornece DY anual direto
                    "ebitda": ativo_data.get("ebitda"),
                    "lucro_liquido": ativo_data.get("netIncome"),
                    "receita": ativo_data.get("totalRevenue"),
                    "market_cap": ativo_data.get("marketCap"),
                    "beta": ativo_data.get("beta"),
                    "setor": ativo_data.get("sector"),
                    "timestamp": ativo_data.get("regularMarketTime"),
                }

                self.cache[ticker] = resultado
                return resultado
            else:
                return None

        except Exception as e:
            print(f"⚠️  Erro ao buscar {ticker} na Brapi: {e}")
            return None

    def buscar_fii(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Busca dados específicos de FII"""
        return self.buscar_ativo(ticker)

    def buscar_acao(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Busca dados específicos de Ação"""
        dados = self.buscar_ativo(ticker)
        if dados:
            # Calcular alguns indicadores úteis para ações
            if dados.get("ebitda") and dados.get("market_cap"):
                ev_ebitda = dados["market_cap"] / dados["ebitda"] if dados["ebitda"] > 0 else None
                dados["ev_ebitda"] = ev_ebitda

        return dados

    def listar_cache(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todos os dados em cache"""
        return self.cache


# Instância global
brapi = BrapiClient()


if __name__ == "__main__":
    # Teste
    resultado = brapi.buscar_fii("MXRF11")
    if resultado:
        print(f"MXRF11: {resultado}")
    else:
        print("Erro ao buscar MXRF11")
