import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

from tools.fii_analytics import analisar_fii_completo
from tools.macro_data import macro


class PesquisadorAtivo:
    """Pesquisa e análise de ativos do Brasil e exterior"""

    def __init__(self):
        self.cache = {}
        self.session = requests.Session()

    def analisar_ativo(self, ticker: str, classe: str) -> Dict[str, Any]:
        """
        Análise completa de um ativo baseada em sua classe
        """
        resultado = {
            "ticker": ticker,
            "classe": classe,
            "timestamp": datetime.now().isoformat(),
            "dados": {},
            "interpretacao": None
        }

        if classe == "FII":
            resultado["dados"] = self._buscar_fii(ticker)
        elif classe == "ACAO_BR":
            resultado["dados"] = self._buscar_acao_br(ticker)
        elif classe == "BDR":
            resultado["dados"] = self._buscar_bdr(ticker)
        elif classe == "ETF_BR":
            resultado["dados"] = self._buscar_etf_br(ticker)
        elif classe.startswith("TESOURO"):
            resultado["dados"] = self._buscar_tesouro(ticker, classe)
        elif classe.startswith("RF_"):
            resultado["dados"] = self._buscar_renda_fixa(ticker, classe)
        else:
            resultado["dados"] = self._buscar_generico(ticker)

        return resultado

    def _buscar_fii(self, ticker: str) -> Dict[str, Any]:
        """
        FII (Fundo de Investimento Imobiliário) — Análise Proativa Detalhada
        Busca: yield, P/VP, vacância, liquidez, portfólio CRI, FCF, patrimônio
        """
        dados = {}

        try:
            ativo = yf.Ticker(ticker + ".SA")
            hist = ativo.history(period="1y")

            dados["cotacao_atual"] = ativo.info.get("currentPrice", None)
            dy = self._calcular_dividend_yield(hist)
            dados["dividend_yield_12m"] = dy
            dados["liquidez_media"] = hist["Volume"].mean() if not hist.empty else None

        except Exception as e:
            dados["erro_yfinance"] = str(e)
            dy = None

        # Buscar dados do Status Invest (API pública)
        try:
            dados_status = self._buscar_status_invest_fii(ticker)
            dados.update(dados_status)
        except:
            pass

        # 🆕 Análise Proativa Detalhada do FII
        try:
            macro_dados = macro.obter_todas()
            selic = macro_dados.get("selic", 14.4)
            analise_fii = analisar_fii_completo(ticker, dy_anual=dy, selic=selic)

            # Adicionar dados detalhados
            if analise_fii.get("dados"):
                dados["fii_proativo"] = {
                    "tipo": analise_fii["dados"].get("tipo"),
                    "segmento": analise_fii["dados"].get("segmento"),
                    "gestor": analise_fii["dados"].get("gestor"),
                    "liquidez": analise_fii["dados"].get("liquidez"),
                    "patrimonio": analise_fii["dados"].get("patrimonio"),
                    "vacancia": analise_fii["dados"].get("vacancia"),
                    "portfolio_cri": analise_fii["dados"].get("portfolio_cri"),
                    "fluxo_caixa": analise_fii["dados"].get("fluxo_caixa"),
                    "analise": analise_fii.get("analise")
                }
        except Exception as e:
            dados["erro_fii_proativo"] = str(e)

        return dados

    def _buscar_acao_br(self, ticker: str) -> Dict[str, Any]:
        """
        Ação brasileira
        Busca: valuation (P/L, P/VP, EV/EBITDA), dividendos, fluxo de caixa
        """
        dados = {}

        try:
            ativo = yf.Ticker(ticker + ".SA")
            info = ativo.info
            hist = ativo.history(period="1y")

            dados["cotacao_atual"] = info.get("currentPrice", None)
            dados["setor"] = info.get("sector", None)
            dados["marketcap"] = info.get("marketCap", None)
            dados["p_l"] = info.get("trailingPE", None)
            dados["p_vp"] = info.get("priceToBook", None)
            dados["dividend_yield"] = info.get("dividendYield", None)
            dados["beta"] = info.get("beta", None)
            dados["52_week_high"] = hist["Close"].max() if not hist.empty else None
            dados["52_week_low"] = hist["Close"].min() if not hist.empty else None
            dados["volatilidade_52w"] = hist["Close"].std() if not hist.empty else None

        except Exception as e:
            dados["erro_yfinance"] = str(e)

        return dados

    def _buscar_bdr(self, ticker: str) -> Dict[str, Any]:
        """
        BDR (Brazilian Depositary Receipt)
        Busca: cotação em dólar, câmbio, ativo subjacente, valuation
        """
        dados = {}

        try:
            ativo = yf.Ticker(ticker + ".SA")
            info = ativo.info
            hist = ativo.history(period="1y")

            dados["cotacao_bdr_br"] = info.get("currentPrice", None)
            dados["ativo_subjacente"] = info.get("underlyingSymbol", None)
            dados["p_l"] = info.get("trailingPE", None)
            dados["dividend_yield"] = info.get("dividendYield", None)

            # Buscar cotação do ativo subjacente em USD
            ticker_usd = info.get("underlyingSymbol")
            if ticker_usd:
                try:
                    ativo_usd = yf.Ticker(ticker_usd)
                    dados["cotacao_usd"] = ativo_usd.info.get("currentPrice", None)
                except:
                    pass

            # Câmbio USD/BRL
            try:
                cambio = yf.Ticker("USDBRL=X")
                dados["cambio_usdbrl"] = cambio.info.get("currentPrice", None)
            except:
                pass

        except Exception as e:
            dados["erro_yfinance"] = str(e)

        return dados

    def _buscar_etf_br(self, ticker: str) -> Dict[str, Any]:
        """
        ETF Brasil
        Busca: TER, composição, performance vs benchmark, AUM
        """
        dados = {}

        try:
            ativo = yf.Ticker(ticker + ".SA")
            info = ativo.info
            hist = ativo.history(period="1y")

            dados["cotacao_atual"] = info.get("currentPrice", None)
            dados["aum"] = info.get("totalAssets", None)
            dados["expense_ratio"] = info.get("expenseRatio", None)
            dados["dividend_yield"] = info.get("dividendYield", None)
            dados["performance_1y"] = self._calcular_performance(hist)

        except Exception as e:
            dados["erro_yfinance"] = str(e)

        return dados

    def _buscar_tesouro(self, titulo: str, classe: str) -> Dict[str, Any]:
        """
        Tesouro Direto
        Busca: taxa, duration, posição na curva, comparativo com CDI/IPCA
        """
        dados = {}

        # Tentar buscar dados do Tesouro Direto (API do BCB)
        try:
            # Simulação — em produção seria integrado com API do Tesouro
            dados["tipo"] = classe
            dados["titulo"] = titulo
            # Estes dados viriam da API do Tesouro Direto via BCB
            dados["taxa_compra"] = None
            dados["taxa_venda"] = None
            dados["duration"] = None

        except Exception as e:
            dados["erro"] = str(e)

        return dados

    def _buscar_renda_fixa(self, titulo: str, classe: str) -> Dict[str, Any]:
        """
        Renda Fixa Privada (CDB, LCI, LCA, CRI, CRA, Debêntures, FIDC)
        Busca: taxa, duration, risco de crédito do emissor
        """
        dados = {}

        tipo = classe.replace("RF_", "")
        dados["tipo"] = tipo
        dados["titulo"] = titulo
        # Dados que viriam de APIs de instituições financeiras
        dados["taxa"] = None
        dados["duration"] = None
        dados["spread_cdi"] = None
        dados["risco_credito"] = None

        return dados

    def _buscar_generico(self, ticker: str) -> Dict[str, Any]:
        """
        Busca genérica para ativos não classificados
        """
        dados = {}

        try:
            ativo = yf.Ticker(ticker)
            info = ativo.info
            hist = ativo.history(period="1y")

            dados["cotacao"] = info.get("currentPrice", None)
            dados["moeda"] = info.get("currency", None)
            dados["performance_1y"] = self._calcular_performance(hist)

        except Exception as e:
            dados["erro"] = str(e)

        return dados

    def _buscar_status_invest_fii(self, ticker: str) -> Dict[str, Any]:
        """
        Busca dados adicionais do Status Invest para FII
        """
        dados = {}

        # Exemplo de integração com API do Status Invest (se disponível)
        # Em produção, seria feita a integração real
        try:
            url = f"https://www.statusinvest.com.br/api/fiis/{ticker}"
            # response = self.session.get(url, timeout=5)
            # dados = response.json()
        except:
            pass

        return dados

    def calcular_indicadores(self, historico: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula indicadores técnicos a partir do histórico de preços
        """
        if historico.empty:
            return {}

        indicadores = {}

        # Média móvel simples
        indicadores["sma_20"] = historico["Close"].rolling(20).mean().iloc[-1]
        indicadores["sma_50"] = historico["Close"].rolling(50).mean().iloc[-1]
        indicadores["sma_200"] = historico["Close"].rolling(200).mean().iloc[-1]

        # RSI (Relative Strength Index)
        indicadores["rsi_14"] = self._calcular_rsi(historico["Close"], 14)

        # MACD
        macd_data = self._calcular_macd(historico["Close"])
        indicadores["macd"] = macd_data

        # Bollinger Bands
        bb_data = self._calcular_bollinger_bands(historico["Close"], 20)
        indicadores["bollinger_bands"] = bb_data

        # Volatilidade
        indicadores["volatilidade_20d"] = historico["Close"].pct_change().rolling(20).std().iloc[-1]

        return indicadores

    def _calcular_rsi(self, precos: pd.Series, periodo: int = 14) -> Optional[float]:
        """Calcula RSI (Relative Strength Index)"""
        try:
            delta = precos.diff()
            ganho = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
            perda = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
            rs = ganho / perda
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except:
            return None

    def _calcular_macd(self, precos: pd.Series) -> Dict[str, Optional[float]]:
        """Calcula MACD (Moving Average Convergence Divergence)"""
        try:
            ema_12 = precos.ewm(span=12).mean()
            ema_26 = precos.ewm(span=26).mean()
            macd = ema_12 - ema_26
            sinal = macd.ewm(span=9).mean()
            histograma = macd - sinal

            return {
                "macd": float(macd.iloc[-1]),
                "sinal": float(sinal.iloc[-1]),
                "histograma": float(histograma.iloc[-1])
            }
        except:
            return {"macd": None, "sinal": None, "histograma": None}

    def _calcular_bollinger_bands(self, precos: pd.Series, periodo: int = 20) -> Dict[str, Optional[float]]:
        """Calcula Bollinger Bands"""
        try:
            media = precos.rolling(periodo).mean()
            desvio = precos.rolling(periodo).std()
            banda_superior = media + (desvio * 2)
            banda_inferior = media - (desvio * 2)

            return {
                "media": float(media.iloc[-1]),
                "superior": float(banda_superior.iloc[-1]),
                "inferior": float(banda_inferior.iloc[-1])
            }
        except:
            return {"media": None, "superior": None, "inferior": None}

    def _calcular_dividend_yield(self, historico: pd.DataFrame) -> Optional[float]:
        """Calcula dividend yield baseado no histórico"""
        try:
            if "Dividends" not in historico.columns:
                return None
            dividendos_12m = historico["Dividends"].tail(252).sum()  # 252 dias úteis = 1 ano
            preco_atual = historico["Close"].iloc[-1]
            return (dividendos_12m / preco_atual) * 100 if preco_atual > 0 else None
        except:
            return None

    def _calcular_performance(self, historico: pd.DataFrame) -> Optional[float]:
        """Calcula performance do ativo"""
        try:
            if historico.empty or len(historico) < 2:
                return None
            preco_inicial = historico["Close"].iloc[0]
            preco_final = historico["Close"].iloc[-1]
            return ((preco_final - preco_inicial) / preco_inicial) * 100
        except:
            return None

    def comparar_com_benchmark(self, ticker: str, benchmark: str) -> Dict[str, Any]:
        """
        Compara performance de um ativo com seu benchmark
        """
        try:
            ativo = yf.Ticker(ticker)
            bench = yf.Ticker(benchmark)

            hist_ativo = ativo.history(period="1y")
            hist_bench = bench.history(period="1y")

            perf_ativo = self._calcular_performance(hist_ativo)
            perf_bench = self._calcular_performance(hist_bench)

            return {
                "ativo": ticker,
                "benchmark": benchmark,
                "performance_ativo": perf_ativo,
                "performance_benchmark": perf_bench,
                "outperformance": (perf_ativo - perf_bench) if perf_ativo and perf_bench else None
            }
        except Exception as e:
            return {"erro": str(e)}


# Instância global
pesquisador = PesquisadorAtivo()


def analisar_ativo(ticker: str, classe: str) -> Dict[str, Any]:
    """Interface pública para análise de ativo"""
    return pesquisador.analisar_ativo(ticker, classe)


def obter_fundamentais_acao(ticker: str) -> Dict[str, Any]:
    """Obtém dados fundamentalistas de uma ação brasileira"""
    return pesquisador._buscar_acao_br(ticker)


def calcular_indicadores(ticker: str) -> Dict[str, Any]:
    """Calcula indicadores técnicos de um ativo"""
    try:
        ativo = yf.Ticker(ticker + ".SA")
        hist = ativo.history(period="1y")
        return pesquisador.calcular_indicadores(hist)
    except Exception as e:
        return {"erro": str(e)}


def comparar_benchmarks(ticker: str, benchmark: str) -> Dict[str, Any]:
    """Compara performance com benchmark"""
    return pesquisador.comparar_com_benchmark(ticker, benchmark)
