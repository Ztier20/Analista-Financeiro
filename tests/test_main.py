"""
Testes para main.py
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from main import analisar_carteira_completa, gerar_resumo, salvar_resultado


class TestAnalisarCarteiraCompleta:
    """Testes para orquestração completa"""

    @patch('main.analisar_ativo')
    @patch('main.ler_extrato_b3')
    def test_analisar_carteira_com_sucesso(self, mock_parser, mock_pesquisa):
        """Testa análise completa com sucesso"""
        # Setup mocks
        mock_carteira = {
            "ACAO_BR": [
                {"ticker": "PETR4", "descricao": "PETR4", "classe": "ACAO_BR"}
            ]
        }
        mock_parser.return_value = mock_carteira

        mock_pesquisa.return_value = {
            "ticker": "PETR4",
            "classe": "ACAO_BR",
            "dados": {"cotacao": 25.30}
        }

        resultado = analisar_carteira_completa("dummy.xlsx")

        assert "timestamp" in resultado
        assert "arquivo_origem" in resultado
        assert "carteira_estruturada" in resultado
        assert "analises" in resultado
        assert "resumo" in resultado

    @patch('main.analisar_ativo')
    @patch('main.ler_extrato_b3')
    def test_trata_erro_em_ativo(self, mock_parser, mock_pesquisa):
        """Testa tratamento de erro em ativo individual"""
        mock_carteira = {
            "ACAO_BR": [
                {"ticker": "PETR4", "descricao": "PETR4", "classe": "ACAO_BR"}
            ]
        }
        mock_parser.return_value = mock_carteira

        # Simula erro na busca
        mock_pesquisa.side_effect = Exception("Erro na API")

        resultado = analisar_carteira_completa("dummy.xlsx")

        assert "analises" in resultado
        assert "ACAO_BR" in resultado["analises"]
        assert len(resultado["analises"]["ACAO_BR"]) > 0
        assert "erro" in resultado["analises"]["ACAO_BR"][0]


class TestGerarResumo:
    """Testes para geração de resumo"""

    def test_gera_resumo_vazio(self):
        """Testa geração de resumo com carteira vazia"""
        carteira = {}
        analises = {}

        resumo = gerar_resumo(carteira, analises)

        assert resumo["total_classes"] == 0
        assert resumo["total_ativos"] == 0
        assert resumo["alertas"] == []

    def test_gera_resumo_multiplas_classes(self, sample_carteira):
        """Testa geração de resumo com múltiplas classes"""
        analises = {
            "FII": [{"ticker": "HGLG11", "classe": "FII", "dados": {}}],
            "ACAO_BR": [{"ticker": "PETR4", "classe": "ACAO_BR", "dados": {}}],
            "TESOURO_SELIC": [{"ticker": "SELIC", "classe": "TESOURO_SELIC", "dados": {}}]
        }

        resumo = gerar_resumo(sample_carteira, analises)

        assert resumo["total_classes"] == 3
        assert resumo["total_ativos"] == 3
        assert resumo["distribuicao_por_classe"]["FII"] == 1
        assert resumo["distribuicao_por_classe"]["ACAO_BR"] == 1
        assert resumo["distribuicao_por_classe"]["TESOURO_SELIC"] == 1

    def test_detecta_alertas_de_erro(self, sample_carteira):
        """Testa detecção de alertas de erro"""
        analises = {
            "FII": [{"ticker": "HGLG11", "classe": "FII", "erro": "API indisponível"}],
            "ACAO_BR": [{"ticker": "PETR4", "classe": "ACAO_BR", "dados": {}}]
        }

        resumo = gerar_resumo(sample_carteira, analises)

        assert len(resumo["alertas"]) == 1
        assert resumo["alertas"][0]["tipo"] == "erro_busca"
        assert resumo["alertas"][0]["ticker"] == "HGLG11"

    def test_resumo_sem_alertas(self, sample_carteira):
        """Testa resumo sem alertas"""
        analises = {
            "FII": [{"ticker": "HGLG11", "classe": "FII", "dados": {}}]
        }

        resumo = gerar_resumo(sample_carteira, analises)

        assert len(resumo["alertas"]) == 0


class TestSalvarResultado:
    """Testes para salvamento de resultados"""

    def test_salva_resultado_json(self, tmp_path, monkeypatch):
        """Testa salvamento de resultado em JSON"""
        # Mudar para tmp_path para não poluir o projeto
        monkeypatch.chdir(tmp_path)

        resultado = {
            "timestamp": "2024-01-01T12:00:00",
            "arquivo_origem": "test.xlsx",
            "carteira_estruturada": {},
            "analises": {},
            "resumo": {}
        }

        salvar_resultado(resultado)

        arquivo = tmp_path / "data" / "analise_completa.json"
        assert arquivo.exists()

        with open(arquivo) as f:
            dados_salvos = json.load(f)

        assert dados_salvos["timestamp"] == resultado["timestamp"]
        assert dados_salvos["arquivo_origem"] == resultado["arquivo_origem"]

    def test_cria_diretorio_se_nao_existir(self, tmp_path, monkeypatch):
        """Testa criação de diretório data/ se não existir"""
        monkeypatch.chdir(tmp_path)

        resultado = {
            "timestamp": "2024-01-01T12:00:00",
            "arquivo_origem": "test.xlsx",
            "carteira_estruturada": {},
            "analises": {},
            "resumo": {}
        }

        assert not (tmp_path / "data").exists()
        salvar_resultado(resultado)
        assert (tmp_path / "data").exists()

    def test_salva_com_encoding_utf8(self, tmp_path, monkeypatch):
        """Testa salvamento com UTF-8 encoding"""
        monkeypatch.chdir(tmp_path)

        resultado = {
            "timestamp": "2024-01-01T12:00:00",
            "arquivo_origem": "test.xlsx",
            "carteira_estruturada": {
                "ACAO_BR": [
                    {"ticker": "PETR4", "descricao": "Ação com acentuação"}
                ]
            },
            "analises": {},
            "resumo": {}
        }

        salvar_resultado(resultado)

        arquivo = tmp_path / "data" / "analise_completa.json"
        with open(arquivo, encoding="utf-8") as f:
            conteudo = f.read()

        assert "acentuação" in conteudo
