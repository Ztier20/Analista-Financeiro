#!/usr/bin/env python3
"""
Relatório Analista Financeiro
Orquestra: parseia → macro → análise → recomendação
"""

import sys
import json
from pathlib import Path
from datetime import datetime

from tools.parser_b3 import ler_extrato_b3, resumo_carteira
from tools.macro_data import macro
from tools.asset_research import analisar_ativo
from tools.brapi_client import brapi
from tools.interpretador import Interpretador
from tools.scorer import calcular_score_por_classe
from tools.consolidacao import (
    analisar_concentracao,
    gerar_alertas_estrategicos,
    gerar_resumo_consolidado
)


def gerar_relatorio(arquivo_extrato: str):
    """Gera relatório completo com recomendações"""

    print(f"\n📊 ANALISTA FINANCEIRO — RELATÓRIO COMPLETO")
    print(f"=" * 70)

    # 1. Parsear extrato
    print(f"\n1️⃣  Lendo extrato...")
    carteira = ler_extrato_b3(arquivo_extrato)
    total_ativos = sum(len(v) for v in carteira.values())
    print(f"   ✓ {total_ativos} ativos encontrados\n")

    # 2. Obter contexto macro
    print(f"2️⃣  Obtendo contexto macroeconômico...")
    macro_dados = macro.obter_todas()
    print(macro.resumo())
    print()

    # 3. Inicializar interpretador
    interpretador = Interpretador(macro_dados)

    # 4. Analisar cada ativo
    print(f"3️⃣  Analisando {total_ativos} ativos...\n")

    relatorio_ativos = []
    contador = 0

    for classe, ativos in carteira.items():
        print(f"📌 {classe}")
        print("-" * 70)

        for ativo in ativos:
            contador += 1
            ticker = ativo["ticker"]
            print(f"   [{contador}/{total_ativos}] {ticker}... ", end="", flush=True)

            try:
                # Buscar dados via yfinance (existente)
                dados_yf = analisar_ativo(ticker, classe)

                # Buscar dados via Brapi (novo) — com fallback
                try:
                    dados_brapi = brapi.buscar_ativo(ticker)
                except:
                    dados_brapi = None

                # Calcular score de qualidade
                score_info = calcular_score_por_classe(
                    classe,
                    ticker,
                    dados_yf.get("dados") if dados_yf else {},
                    macro_dados,
                    ativo.get("valor_total", 0)
                )

                # Gerar interpretação
                if classe == "FII":
                    # Distinguir papel vs tijolo (simplificado: papel se ticker em lista conhecida)
                    fiis_papel = ["DEVA11", "MXRF11", "RBRY11", "VGHF11", "KNSC11", "XPSF11", "SNAG11", "RZAG11"]
                    if ticker in fiis_papel:
                        rec, anl = interpretador.interpretar_fii_papel(
                            ticker,
                            dados_brapi=dados_brapi,
                            dados_yf=dados_yf.get("dados") if dados_yf else None
                        )
                    else:
                        rec, anl = interpretador.interpretar_fii_tijolo(
                            ticker,
                            dados_brapi=dados_brapi,
                            dados_yf=dados_yf.get("dados") if dados_yf else None
                        )

                elif classe == "ACAO_BR":
                    setor = dados_yf.get("dados", {}).get("setor") if dados_yf else None
                    rec, anl = interpretador.interpretar_acao_br(
                        ticker,
                        setor=setor,
                        dados_brapi=dados_brapi,
                        dados_yf=dados_yf.get("dados") if dados_yf else None
                    )

                elif "TESOURO" in classe:
                    valor = ativo.get("valor_total", 0)
                    rec, anl = interpretador.interpretar_tesouro(
                        ticker,
                        tipo=classe,
                        valor_total=valor
                    )

                elif classe == "RENDA_FIXA_PRIVADA":
                    rec, anl = interpretador.interpretar_cdb(
                        ticker,
                        taxa_contratada=None  # Não temos os dados do contrato
                    )

                elif classe == "ETF_BR":
                    rec, anl = interpretador.interpretar_etf(
                        ticker,
                        dados_yf=dados_yf.get("dados") if dados_yf else None
                    )

                else:
                    rec = "MANTENHA"
                    anl = "Sem dados específicos"

                print(f"✓ {rec}")

                relatorio_ativos.append({
                    "ticker": ticker,
                    "classe": classe,
                    "recomendacao": rec,
                    "analise": anl,
                    "score": score_info.get("score", 5) if score_info else 5,
                    "valor_total": ativo.get("valor_total", 0),
                    "dados_yf": dados_yf,
                    "dados_brapi": dados_brapi
                })

            except Exception as e:
                print(f"✗ Erro: {str(e)[:50]}")
                relatorio_ativos.append({
                    "ticker": ticker,
                    "classe": classe,
                    "recomendacao": "N/A",
                    "analise": f"Erro: {str(e)}",
                    "valor_total": ativo.get("valor_total", 0),
                    "score": 0,
                    "erro": str(e)
                })

        print()

    # 5. Análise consolidada
    print(f"4️⃣  Analisando concentração e gerando alertas...")
    concentracao = analisar_concentracao(carteira, relatorio_ativos)
    alertas = gerar_alertas_estrategicos(concentracao, relatorio_ativos, macro_dados)
    resumo_consolidado = gerar_resumo_consolidado(concentracao, alertas, carteira)
    if alertas:
        print(f"   ⚠️  {len(alertas)} alerta(s) identificado(s)")
    else:
        print(f"   ✓ Carteira bem diversificada")
    print()

    # 6. Gerar markdown e salvar
    print(f"5️⃣  Gerando relatório markdown...")
    markdown = gerar_markdown(relatorio_ativos, macro_dados, carteira, resumo_consolidado)

    caminho_relatorio = Path("data/relatorio_analise.md")
    caminho_relatorio.parent.mkdir(exist_ok=True)

    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"   ✓ Salvo em {caminho_relatorio}\n")

    # 7. Resumo final
    print(f"\n" + "=" * 70)
    print(f"✅ ANÁLISE COMPLETA")
    print(f"=" * 70)
    print(f"Total de ativos: {len(relatorio_ativos)}")
    print(f"Recomendações:")
    for rec in ["AUMENTE", "MANTENHA", "REDUZA", "VENDA", "N/A"]:
        qtd = sum(1 for r in relatorio_ativos if r.get("recomendacao") == rec)
        if qtd > 0:
            print(f"  • {rec}: {qtd}")


def gerar_markdown(relatorio: list, macro_dados: dict, carteira: dict, resumo_consolidado: str = "") -> str:
    """Gera relatório em Markdown"""

    md = f"""# 📊 RELATÓRIO ANALISTA FINANCEIRO

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 📈 Contexto Macroeconômico

| Indicador | Valor |
|---|---|
| **Selic** | {macro_dados.get('selic', 'N/A'):.2f}% a.a. |
| **IPCA 12m** | {macro_dados.get('ipca_12m', 'N/A'):.2f}% a.a. |
| **CDI** | {macro_dados.get('cdi', 'N/A'):.2f}% a.a. |
| **Taxa Real (Selic - IPCA)** | {macro_dados.get('selic', 0) - macro_dados.get('ipca_12m', 0):.2f}% |
| **USD/BRL** | R$ {macro_dados.get('usdbrl', 'N/A'):.2f} |

"""

    # Adicionar resumo consolidado se disponível
    if resumo_consolidado:
        md += resumo_consolidado + "\n"

    md += f"""## 💼 Carteira — {sum(len(v) for v in carteira.values())} Ativos

"""

    # Agrupar por classe
    relatorio_por_classe = {}
    for item in relatorio:
        classe = item["classe"]
        if classe not in relatorio_por_classe:
            relatorio_por_classe[classe] = []
        relatorio_por_classe[classe].append(item)

    # Gerar seções por classe
    for classe in sorted(relatorio_por_classe.keys()):
        ativos = relatorio_por_classe[classe]
        md += f"\n### {classe} ({len(ativos)} ativo(s))\n\n"

        for item in sorted(ativos, key=lambda x: x["ticker"]):
            ticker = item["ticker"]
            rec = item.get("recomendacao", "N/A")
            anl = item.get("analise", "N/A")

            # Score pode ser float ou dict
            score_data = item.get("score")
            if isinstance(score_data, dict):
                score = score_data.get("score", "N/A")
                categoria = score_data.get("categoria", "N/A")
            else:
                score = score_data if score_data is not None else "N/A"
                categoria = "N/A"

            # Emoji por recomendação
            emoji = {
                "AUMENTE": "📈",
                "MANTENHA": "➡️",
                "REDUZA": "📉",
                "VENDA": "⛔",
                "N/A": "❓"
            }.get(rec, "❓")

            # Emoji por score
            if isinstance(score, (int, float)):
                score_emoji = "⭐" if score >= 8 else "✓" if score >= 6 else "◆" if score >= 4 else "!"
            else:
                score_emoji = "?"

            md += f"#### {emoji} {ticker} — {score_emoji} Score: {score}\n\n"
            md += f"**Categoria:** {categoria} | **Recomendação:** `{rec}`\n\n"

            # Detalhes do score
            if isinstance(score_data, dict) and "detalhes" not in str(score_data):
                details = []
                for k, v in score_data.items():
                    if k not in ["score", "categoria", "ticker", "classe", "detalhes"]:
                        details.append(f"- {k}: {v}")
                if details:
                    md += "**Detalhes:**\n" + "\n".join(details) + "\n\n"

            md += f"{anl}\n\n"
            md += "---\n\n"

    # Rodapé
    md += f"""
## 📝 Sumário de Recomendações

"""

    for rec_tipo in ["AUMENTE", "MANTENHA", "REDUZA", "VENDA"]:
        qtd = sum(1 for r in relatorio if r.get("recomendacao") == rec_tipo)
        if qtd > 0:
            md += f"- **{rec_tipo}**: {qtd} ativo(s)\n"

    md += f"""

---

*Relatório gerado automaticamente pelo Analista Financeiro*
*Dados em tempo real via yfinance, Brapi e BCB Open Data*
"""

    return md


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 relatorio.py <arquivo_extrato_b3.xlsx>")
        print("\nExemplo:")
        print("  python3 relatorio.py posicao_2026.xlsx")
        sys.exit(1)

    arquivo = sys.argv[1]

    if not Path(arquivo).exists():
        print(f"❌ Arquivo não encontrado: {arquivo}")
        sys.exit(1)

    try:
        gerar_relatorio(arquivo)
    except Exception as e:
        print(f"\n❌ Erro durante geração do relatório: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
