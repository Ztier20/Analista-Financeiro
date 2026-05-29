"""
Testes para parser_b3.py
"""

import pytest
from tools.parser_b3 import (
    classificar_ativo,
    identificar_classe,
    organizar_por_classe,
    resumo_carteira
)


class TestClassificarAtivo:
    """Testes para classificação de ativos"""

    def test_classifica_fii(self):
        resultado = classificar_ativo("HGLG11 FUNDO INV IMOB")
        assert resultado["ticker"] == "HGLG11"
        assert resultado["classe"] == "FII"

    def test_classifica_acao_br(self):
        resultado = classificar_ativo("PETR4 PETROBRAS PN")
        assert resultado["ticker"] == "PETR4"
        assert resultado["classe"] == "ACAO_BR"

    def test_classifica_bdr(self):
        resultado = classificar_ativo("BBDC34 BDR BBDC")
        assert resultado["ticker"] == "BBDC34"
        assert resultado["classe"] == "BDR"

    def test_classifica_etf_br(self):
        resultado = classificar_ativo("BOVA11 ISHARES BOVESPA")
        assert resultado["ticker"] == "BOVA11"
        assert resultado["classe"] == "ETF_BR"

    def test_classifica_tesouro_selic(self):
        resultado = classificar_ativo("TESOURO SELIC 2025")
        assert resultado["classe"] == "TESOURO_SELIC"

    def test_classifica_tesouro_ipca(self):
        resultado = classificar_ativo("TESOURO IPCA+ 2035")
        assert resultado["classe"] == "TESOURO_IPCA"

    def test_classifica_tesouro_prefixado(self):
        resultado = classificar_ativo("TESOURO PREFIXADO 2030")
        assert resultado["classe"] == "TESOURO_PREFIXADO"

    def test_rejeita_vazio(self):
        resultado = classificar_ativo("")
        assert resultado is None

    def test_rejeita_nan(self):
        resultado = classificar_ativo("NaN")
        assert resultado is None


class TestIdentificarClasse:
    """Testes para identificação de classe por ticker"""

    def test_identifica_fii_por_ticker(self):
        classe = identificar_classe("HGLG11", "HGLG11 FUNDO INV IMOB")
        assert classe == "FII"

    def test_identifica_acao_br_por_ticker(self):
        classe = identificar_classe("PETR4", "PETR4 PETROBRAS PN")
        assert classe == "ACAO_BR"

    def test_identifica_bdr_por_ticker(self):
        classe = identificar_classe("BBDC34", "BDR BBDC")
        assert classe == "BDR"

    def test_identifica_etf_br_por_ticker(self):
        classe = identificar_classe("BOVA11", "ISHARES BOVESPA")
        assert classe == "ETF_BR"

    def test_identifica_tesouro_por_descricao(self):
        classe = identificar_classe("XXX", "TESOURO SELIC 2025")
        assert classe == "TESOURO_SELIC"

    def test_identifica_renda_fixa_privada(self):
        classe = identificar_classe("ABC123", "CDB 100% CDI")
        assert classe == "RF_CDB"

    def test_identifica_outro(self):
        classe = identificar_classe("XXXXX", "PRODUTO DESCONHECIDO")
        assert classe == "OUTRO"


class TestOrganizarPorClasse:
    """Testes para organização de carteira por classe"""

    def test_organiza_carteira_vazia(self):
        resultado = organizar_por_classe([])
        assert len(resultado) == 0

    def test_organiza_carteira_unica_classe(self):
        ativos = [
            {"ticker": "PETR4", "descricao": "PETR4", "classe": "ACAO_BR"},
            {"ticker": "VALE3", "descricao": "VALE3", "classe": "ACAO_BR"}
        ]
        resultado = organizar_por_classe(ativos)
        assert len(resultado) == 1
        assert "ACAO_BR" in resultado
        assert len(resultado["ACAO_BR"]) == 2

    def test_organiza_carteira_multiplas_classes(self, sample_carteira):
        ativos = []
        for classe, lista in sample_carteira.items():
            ativos.extend(lista)

        resultado = organizar_por_classe(ativos)
        assert len(resultado) == 3
        assert all(classe in resultado for classe in ["FII", "ACAO_BR", "TESOURO_SELIC"])

    def test_agrupa_renda_fixa_privada(self):
        ativos = [
            {"ticker": "CDB1", "descricao": "CDB 100% CDI", "classe": "RF_CDB"},
            {"ticker": "LCI1", "descricao": "LCI 100% CDI", "classe": "RF_LCI"}
        ]
        resultado = organizar_por_classe(ativos)
        assert "RENDA_FIXA_PRIVADA" in resultado
        assert len(resultado["RENDA_FIXA_PRIVADA"]) == 2

    def test_remove_classes_vazias(self):
        ativos = [
            {"ticker": "PETR4", "descricao": "PETR4", "classe": "ACAO_BR"}
        ]
        resultado = organizar_por_classe(ativos)
        assert all(len(v) > 0 for v in resultado.values())


class TestResumoCarteira:
    """Testes para geração de resumo em texto"""

    def test_resumo_carteira_vazia(self):
        carteira = {}
        resultado = resumo_carteira(carteira)
        assert "CARTEIRA ESTRUTURADA" in resultado
        assert "Total de ativos: 0" in resultado

    def test_resumo_carteira_populada(self, sample_carteira):
        resultado = resumo_carteira(sample_carteira)
        assert "CARTEIRA ESTRUTURADA" in resultado
        assert "Total de ativos: 3" in resultado
        assert "HGLG11" in resultado
        assert "PETR4" in resultado
        assert "SELIC" in resultado

    def test_resumo_inclui_quantidades(self, sample_carteira):
        resultado = resumo_carteira(sample_carteira)
        assert "Qtd: 100" in resultado
        assert "Qtd: 50" in resultado

    def test_resumo_inclui_valores(self, sample_carteira):
        resultado = resumo_carteira(sample_carteira)
        assert "15050.0" in resultado or "15050" in resultado
