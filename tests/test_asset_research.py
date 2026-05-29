"""
Testes para asset_research.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from tools.asset_research import PesquisadorAtivo, analisar_ativo


class TestPesquisadorAtivo:
    """Testes para a classe PesquisadorAtivo"""

    def test_inicializa_pesquisador(self):
        pesquisador = PesquisadorAtivo()
        assert pesquisador.cache == {}
        assert pesquisador.session is not None

    @patch('tools.asset_research.yf.Ticker')
    def test_analisar_acao_br(self, mock_ticker):
        """Testa análise de ação brasileira com mock"""
        mock_ativo = MagicMock()
        mock_ativo.info = {
            "currentPrice": 25.30,
            "sector": "Energia",
            "marketCap": 150000000000,
            "trailingPE": 8.5,
            "priceToBook": 1.2,
            "dividendYield": 0.05,
            "beta": 1.1
        }
        mock_ativo.history.return_value = pd.DataFrame({
            "Close": [20.0, 22.0, 24.0, 25.30],
            "Volume": [1000000, 1100000, 1200000, 1150000]
        })
        mock_ticker.return_value = mock_ativo

        pesquisador = PesquisadorAtivo()
        resultado = pesquisador._buscar_acao_br("PETR4")

        assert resultado["cotacao_atual"] == 25.30
        assert resultado["setor"] == "Energia"
        assert resultado["p_l"] == 8.5
        assert resultado["dividend_yield"] == 0.05

    @patch('tools.asset_research.yf.Ticker')
    def test_analisar_fii(self, mock_ticker):
        """Testa análise de FII com mock"""
        mock_ativo = MagicMock()
        mock_ativo.info = {"currentPrice": 150.50}
        mock_ativo.history.return_value = pd.DataFrame({
            "Close": [145.0, 148.0, 150.50],
            "Volume": [500000, 600000, 550000],
            "Dividends": [0.0, 1.25, 0.0]
        })
        mock_ticker.return_value = mock_ativo

        pesquisador = PesquisadorAtivo()
        resultado = pesquisador._buscar_fii("HGLG11")

        assert resultado["cotacao_atual"] == 150.50
        assert "liquidez_media" in resultado

    def test_analisar_ativo_fii(self):
        """Testa orquestração de análise para FII"""
        pesquisador = PesquisadorAtivo()
        with patch.object(pesquisador, '_buscar_fii', return_value={"cotacao": 150}):
            resultado = pesquisador.analisar_ativo("HGLG11", "FII")

            assert resultado["ticker"] == "HGLG11"
            assert resultado["classe"] == "FII"
            assert "timestamp" in resultado
            assert "dados" in resultado

    def test_analisar_ativo_acao_br(self):
        """Testa orquestração de análise para ação"""
        pesquisador = PesquisadorAtivo()
        with patch.object(pesquisador, '_buscar_acao_br', return_value={"cotacao": 25.30}):
            resultado = pesquisador.analisar_ativo("PETR4", "ACAO_BR")

            assert resultado["ticker"] == "PETR4"
            assert resultado["classe"] == "ACAO_BR"
            assert "timestamp" in resultado

    def test_analisar_ativo_bdr(self):
        """Testa orquestração de análise para BDR"""
        pesquisador = PesquisadorAtivo()
        with patch.object(pesquisador, '_buscar_bdr', return_value={"cotacao_bdr": 45}):
            resultado = pesquisador.analisar_ativo("BBDC34", "BDR")

            assert resultado["classe"] == "BDR"

    def test_analisar_ativo_etf_br(self):
        """Testa orquestração de análise para ETF"""
        pesquisador = PesquisadorAtivo()
        with patch.object(pesquisador, '_buscar_etf_br', return_value={"aum": 1000000}):
            resultado = pesquisador.analisar_ativo("BOVA11", "ETF_BR")

            assert resultado["classe"] == "ETF_BR"


class TestIndicadores:
    """Testes para cálculo de indicadores técnicos"""

    def test_calcula_rsi(self):
        """Testa cálculo de RSI"""
        pesquisador = PesquisadorAtivo()
        precos = pd.Series([45.0, 46.0, 45.5, 47.0, 48.0, 47.5, 49.0, 50.0])
        rsi = pesquisador._calcular_rsi(precos, periodo=5)

        assert rsi is not None
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_calcula_macd(self):
        """Testa cálculo de MACD"""
        pesquisador = PesquisadorAtivo()
        precos = pd.Series(range(50, 100))  # Série crescente
        macd = pesquisador._calcular_macd(precos)

        assert "macd" in macd
        assert "sinal" in macd
        assert "histograma" in macd
        assert macd["macd"] is not None

    def test_calcula_bollinger_bands(self):
        """Testa cálculo de Bollinger Bands"""
        pesquisador = PesquisadorAtivo()
        precos = pd.Series([45.0, 46.0, 45.5, 47.0, 48.0, 47.5, 49.0, 50.0])
        bb = pesquisador._calcular_bollinger_bands(precos, periodo=5)

        assert "media" in bb
        assert "superior" in bb
        assert "inferior" in bb
        assert bb["superior"] > bb["media"] > bb["inferior"]

    def test_calcula_dividend_yield(self):
        """Testa cálculo de dividend yield"""
        pesquisador = PesquisadorAtivo()
        hist = pd.DataFrame({
            "Close": [100.0] * 252,
            "Dividends": [0.0] * 250 + [5.0, 0.0]
        })
        dy = pesquisador._calcular_dividend_yield(hist)

        assert dy is not None
        assert dy > 0

    def test_calcula_performance(self):
        """Testa cálculo de performance"""
        pesquisador = PesquisadorAtivo()
        hist = pd.DataFrame({
            "Close": [100.0, 105.0, 110.0, 115.0]
        })
        perf = pesquisador._calcular_performance(hist)

        assert perf == 15.0  # (115-100)/100 * 100 = 15%

    def test_calcular_indicadores_vazio(self):
        """Testa cálculo com histórico vazio"""
        pesquisador = PesquisadorAtivo()
        resultado = pesquisador.calcular_indicadores(pd.DataFrame())

        assert resultado == {}


class TestComparacaoBenchmark:
    """Testes para comparação com benchmarks"""

    def test_compara_com_benchmark(self):
        """Testa comparação de performance com benchmark"""
        pesquisador = PesquisadorAtivo()

        hist_ativo = pd.DataFrame({
            "Close": [100.0, 110.0, 120.0]
        })
        hist_bench = pd.DataFrame({
            "Close": [100.0, 105.0, 108.0]
        })

        with patch('tools.asset_research.yf.Ticker') as mock_ticker:
            mock_ativo = MagicMock()
            mock_bench = MagicMock()

            mock_ticker.side_effect = [mock_ativo, mock_bench]
            mock_ativo.history.return_value = hist_ativo
            mock_bench.history.return_value = hist_bench

            resultado = pesquisador.comparar_com_benchmark("PETR4", "IBOVESPA")

            assert "performance_ativo" in resultado
            assert "performance_benchmark" in resultado
            assert "outperformance" in resultado
            assert resultado["performance_ativo"] == 20.0
            assert resultado["performance_benchmark"] == 8.0


class TestInterfacePublica:
    """Testes para funções públicas da API"""

    def test_analisar_ativo_interface(self):
        """Testa função pública analisar_ativo"""
        with patch('tools.asset_research.pesquisador.analisar_ativo') as mock:
            mock.return_value = {"ticker": "PETR4", "classe": "ACAO_BR"}
            resultado = analisar_ativo("PETR4", "ACAO_BR")

            assert resultado["ticker"] == "PETR4"
