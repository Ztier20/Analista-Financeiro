"""
Fixtures compartilhadas para testes
"""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_carteira():
    """
    Carteira estruturada de exemplo para testes
    """
    return {
        "FII": [
            {
                "ticker": "HGLG11",
                "descricao": "HGLG11 FUNDO INV IMOB",
                "classe": "FII",
                "quantidade": 100,
                "preco_medio": 150.50,
                "valor_total": 15050.00
            }
        ],
        "ACAO_BR": [
            {
                "ticker": "PETR4",
                "descricao": "PETR4 PETROBRAS PN",
                "classe": "ACAO_BR",
                "quantidade": 50,
                "preco_medio": 25.30,
                "valor_total": 1265.00
            }
        ],
        "TESOURO_SELIC": [
            {
                "ticker": "SELIC",
                "descricao": "TESOURO SELIC 2025",
                "classe": "TESOURO_SELIC",
                "quantidade": 1000,
                "preco_medio": 100.00,
                "valor_total": 100000.00
            }
        ]
    }


@pytest.fixture
def sample_excel_file(tmp_path):
    """
    Cria um arquivo Excel de exemplo para testes
    """
    data = {
        "PRODUTO": [
            "HGLG11 FUNDO INV IMOB",
            "PETR4 PETROBRAS PN",
            "TESOURO SELIC 2025"
        ],
        "QUANTIDADE": [100, 50, 1000],
        "PREÇO MÉDIO": [150.50, 25.30, 100.00],
        "VALOR ATUALIZADO": [15050.00, 1265.00, 100000.00]
    }

    df = pd.DataFrame(data)
    file_path = tmp_path / "extrato_b3.xlsx"
    df.to_excel(file_path, index=False, engine="openpyxl")

    return str(file_path)


@pytest.fixture
def ativos_teste():
    """
    Lista de ativos para teste individual
    """
    return [
        {"ticker": "HGLG11", "classe": "FII"},
        {"ticker": "PETR4", "classe": "ACAO_BR"},
        {"ticker": "ITUB4", "classe": "ACAO_BR"},
        {"ticker": "BOVA11", "classe": "ETF_BR"},
        {"ticker": "BBDC34", "classe": "BDR"},
    ]
