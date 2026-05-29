#!/usr/bin/env python3
"""
Analista Financeiro Pessoal — Main

Orquestra o fluxo de análise:
1. Parseia extrato B3
2. Busca dados de cada ativo
3. Gera análise consolidada
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from tools.parser_b3 import ler_extrato_b3, resumo_carteira
from tools.asset_research import analisar_ativo


def analisar_carteira_completa(arquivo_extrato: str) -> Dict[str, Any]:
    """
    Executa análise completa da carteira:
    1. Parseia extrato B3
    2. Para cada ativo, busca dados
    3. Consolida análise
    """
    print(f"\n📊 Iniciando análise da carteira...")
    print(f"   Arquivo: {arquivo_extrato}\n")

    # Parsear extrato
    carteira_estruturada = ler_extrato_b3(arquivo_extrato)
    print(resumo_carteira(carteira_estruturada))

    # Analisar cada ativo
    analises = {}
    total_ativos = sum(len(v) for v in carteira_estruturada.values())
    contador = 0

    for classe, ativos in carteira_estruturada.items():
        print(f"\n\n📈 Analisando {classe}...")
        analises[classe] = []

        for ativo in ativos:
            contador += 1
            ticker = ativo["ticker"]
            print(f"   [{contador}/{total_ativos}] {ticker}...", end=" ", flush=True)

            try:
                resultado = analisar_ativo(ticker, classe)
                analises[classe].append(resultado)
                print("✓")
            except Exception as e:
                print(f"✗ (erro: {str(e)[:50]})")
                analises[classe].append({
                    "ticker": ticker,
                    "classe": classe,
                    "erro": str(e)
                })

    # Consolidar resultado
    resultado_final = {
        "timestamp": datetime.now().isoformat(),
        "arquivo_origem": arquivo_extrato,
        "carteira_estruturada": carteira_estruturada,
        "analises": analises,
        "resumo": gerar_resumo(carteira_estruturada, analises)
    }

    # Salvar resultado
    salvar_resultado(resultado_final)

    return resultado_final


def gerar_resumo(carteira: Dict, analises: Dict) -> Dict[str, Any]:
    """
    Gera resumo consolidado da carteira
    """
    resumo = {
        "total_classes": len(carteira),
        "total_ativos": sum(len(v) for v in carteira.values()),
        "distribuicao_por_classe": {},
        "alertas": []
    }

    # Contar ativos por classe
    for classe, ativos in carteira.items():
        resumo["distribuicao_por_classe"][classe] = len(ativos)

    # Identificar problemas
    for classe, resultados_classe in analises.items():
        for resultado in resultados_classe:
            if "erro" in resultado:
                resumo["alertas"].append({
                    "tipo": "erro_busca",
                    "ticker": resultado.get("ticker"),
                    "classe": classe,
                    "mensagem": resultado["erro"]
                })

    return resumo


def salvar_resultado(resultado: Dict[str, Any]):
    """
    Salva análise completa em arquivo JSON
    """
    caminho = Path("data/analise_completa.json")
    caminho.parent.mkdir(exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n\n✅ Análise salva em {caminho}")


def exibir_analise(resultado: Dict[str, Any]):
    """
    Exibe resumo da análise no console
    """
    resumo = resultado["resumo"]

    print("\n" + "=" * 60)
    print("  RESUMO DA ANÁLISE")
    print("=" * 60)
    print(f"\nTotal de ativos: {resumo['total_ativos']}")
    print(f"Classes presentes: {resumo['total_classes']}\n")

    print("Distribuição por classe:")
    for classe, qtd in resumo["distribuicao_por_classe"].items():
        print(f"  • {classe}: {qtd} ativo(s)")

    if resumo["alertas"]:
        print(f"\n⚠️  Alertas ({len(resumo['alertas'])}):")
        for alerta in resumo["alertas"]:
            print(f"  • [{alerta['tipo']}] {alerta['ticker']}: {alerta['mensagem']}")
    else:
        print("\n✓ Nenhum alerta")

    print("\n" + "=" * 60)
    print("Análise completa salva em data/analise_completa.json")
    print("=" * 60 + "\n")


def main():
    """
    Entry point
    """
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo_extrato_b3.xlsx>")
        print("\nExemplo:")
        print("  python main.py extrato_b3_2024.xlsx")
        sys.exit(1)

    arquivo = sys.argv[1]

    # Validar arquivo
    if not Path(arquivo).exists():
        print(f"❌ Arquivo não encontrado: {arquivo}")
        sys.exit(1)

    if not arquivo.lower().endswith((".xlsx", ".xls")):
        print("❌ Arquivo deve ser Excel (.xlsx ou .xls)")
        sys.exit(1)

    try:
        resultado = analisar_carteira_completa(arquivo)
        exibir_analise(resultado)
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
