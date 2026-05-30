"""
Agente Analista Financeiro com IA
Usa Claude via Anthropic SDK para analisar a carteira e recomendar ações
"""

import os
from typing import Dict, List, Optional, Generator
import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """Você é um Analista Financeiro Especialista, não um assistente genérico.

## Perfil do Investidor
- **Perfil de risco:** Moderado
- **Objetivos:** Acumulação de patrimônio no longo prazo + renda passiva mensal
- **Mercados:** Brasil (FIIs, ações, renda fixa) e exterior
- **Postura:** Investidor racional, busca equilíbrio entre crescimento e segurança

## Sua Função
Analisar a carteira completa do investidor e:
1. Identificar os pontos mais críticos que precisam de atenção
2. Recomendar ações concretas (comprar, vender, rebalancear, manter)
3. Justificar cada recomendação com dados da carteira e contexto macro
4. Conectar sempre a análise aos objetivos do investidor: acumulação + renda passiva

## Regras de Análise
- Nunca apenas descreva — sempre interprete e recomende
- Seja direto e técnico, sem enrolação
- Priorize recomendações pelo impacto no patrimônio e na renda passiva
- Considere sempre o custo de oportunidade (ex: FII com DY abaixo da Selic)
- Aponte riscos com clareza, sem catastrofismo
- Quando os dados forem insuficientes, diga claramente

## Framework de Recomendação
Para cada ativo, use:
- **AUMENTE**: ativo bem posicionado, vale ampliar a posição
- **MANTENHA**: ativo adequado, não requer ação imediata
- **REDUZA**: ativo com problemas, considere diminuir exposição
- **VENDA**: ativo inadequado para o perfil ou em deterioração

## Tom e Postura
- Técnico mas direto
- Fale como um analista sênior, não como um chatbot
- Respostas em português do Brasil
- Use markdown para organizar as respostas quando necessário"""


def _construir_contexto(
    analises: Dict,
    macro_dados: Dict,
    alertas: Optional[List] = None,
) -> str:
    """Monta o contexto completo da carteira para o agente"""

    linhas = ["# CONTEXTO DA CARTEIRA DO INVESTIDOR\n"]

    # Macro
    selic = macro_dados.get("selic", 0)
    ipca = macro_dados.get("ipca_12m", 0)
    cdi = macro_dados.get("cdi", 0)
    linhas.append(f"## Contexto Macroeconômico")
    linhas.append(f"- Selic: {selic:.2f}% a.a.")
    linhas.append(f"- IPCA 12m: {ipca:.2f}%")
    linhas.append(f"- CDI: {cdi:.2f}% a.a.")
    linhas.append(f"- Taxa Real (Selic - IPCA): {selic - ipca:.2f}%\n")

    # Resumo da carteira
    total_ativos = sum(len(v) for v in analises.values())
    total_valor = sum(
        a.get("valor") or 0
        for v in analises.values()
        for a in v
    )
    linhas.append(f"## Resumo da Carteira")
    linhas.append(f"- Total de ativos: {total_ativos}")
    linhas.append(f"- Valor total estimado: R$ {total_valor:,.2f}" if total_valor else "- Valor total: não disponível")

    # Distribuição por classe
    linhas.append(f"\n### Distribuição por Classe")
    for classe, ativos in analises.items():
        valor_classe = sum(a.get("valor") or 0 for a in ativos)
        pct = (valor_classe / total_valor * 100) if total_valor > 0 else 0
        linhas.append(f"- {classe}: {len(ativos)} ativo(s) | R$ {valor_classe:,.0f} ({pct:.1f}%)")

    # Scores por ativo
    linhas.append(f"\n## Scores dos Ativos (0-10)")
    for classe, ativos in analises.items():
        linhas.append(f"\n### {classe}")
        for ativo in sorted(ativos, key=lambda x: (x.get("score", {}).get("score") or 0) if isinstance(x.get("score"), dict) else 0, reverse=True):
            ticker = ativo.get("ticker", "N/A")
            score_info = ativo.get("score", {})
            score = score_info.get("score", "N/A") if isinstance(score_info, dict) else "N/A"
            categoria = score_info.get("categoria", "") if isinstance(score_info, dict) else ""
            valor = ativo.get("valor") or 0
            pct = (valor / total_valor * 100) if total_valor > 0 else 0

            # Dados específicos por classe
            dados_yf = ativo.get("dados_yf", {}) or {}
            extras = []

            if classe == "FII":
                dy = dados_yf.get("dividend_yield_12m") or (dados_yf.get("dividend_yield", 0) or 0) * 100
                if dy:
                    extras.append(f"DY {dy:.1f}%")
                    if dy < selic:
                        extras.append("⚠️ DY < Selic")

            elif classe == "ACAO_BR":
                pl = dados_yf.get("p_l")
                dy = (dados_yf.get("dividend_yield") or 0) * 100
                if pl:
                    extras.append(f"P/L {pl:.1f}x")
                if dy:
                    extras.append(f"DY {dy:.1f}%")

            elif "TESOURO" in classe or "RF_" in classe:
                rf = dados_yf.get("rf_proativo", {}) or {}
                taxa = rf.get("taxa_contratada")
                if taxa:
                    extras.append(f"Taxa {taxa:.2f}%")

            extras_str = f" | {', '.join(extras)}" if extras else ""
            score_str = f"{score:.1f}" if isinstance(score, (int, float)) else "N/A"
            linhas.append(f"- **{ticker}**: Score {score_str} ({categoria}) | {pct:.1f}% da carteira{extras_str}")

    # Alertas
    if alertas:
        criticos = [a for a in alertas if a.get("severidade") == "CRÍTICA"]
        altos = [a for a in alertas if a.get("severidade") == "ALTA"]

        if criticos or altos:
            linhas.append(f"\n## Alertas Prioritários")
            for a in (criticos + altos)[:8]:
                emoji = "🔴" if a.get("severidade") == "CRÍTICA" else "🟠"
                linhas.append(f"- {emoji} **{a.get('titulo')}**: {a.get('descricao')}")

    return "\n".join(linhas)


def criar_agente_cliente() -> Optional[anthropic.Anthropic]:
    """Cria cliente Anthropic. Retorna None se API key não configurada."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def chat_com_agente(
    mensagem_usuario: str,
    historico: List[Dict],
    analises: Dict,
    macro_dados: Dict,
    alertas: Optional[List] = None,
) -> Generator[str, None, None]:
    """
    Envia mensagem ao agente e retorna resposta em streaming

    Args:
        mensagem_usuario: Pergunta/comando do usuário
        historico: Lista de mensagens anteriores [{role, content}]
        analises: Dados da carteira do dashboard
        macro_dados: Dados macroeconômicos
        alertas: Lista de alertas ativos

    Yields:
        Chunks de texto da resposta
    """
    client = criar_agente_cliente()
    if not client:
        yield "❌ **ANTHROPIC_API_KEY não configurada.** Configure a variável de ambiente para usar o agente."
        return

    # Contexto da carteira (será cacheado junto com o system prompt)
    contexto = _construir_contexto(analises, macro_dados, alertas)

    system_com_contexto = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": contexto,
            "cache_control": {"type": "ephemeral"},
        },
    ]

    # Montar histórico de mensagens
    messages = list(historico) + [{"role": "user", "content": mensagem_usuario}]

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=system_com_contexto,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.AuthenticationError:
        yield "❌ **API Key inválida.** Verifique a variável ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        yield "⚠️ **Rate limit atingido.** Aguarde alguns segundos e tente novamente."
    except Exception as e:
        yield f"❌ **Erro ao consultar o agente:** {str(e)}"


def gerar_analise_inicial(
    analises: Dict,
    macro_dados: Dict,
    alertas: Optional[List] = None,
) -> Generator[str, None, None]:
    """
    Gera análise inicial automática da carteira ao abrir o agente.
    Pergunta padrão: o que precisa de atenção?
    """
    mensagem = (
        "Analise minha carteira completa. "
        "Identifique os 3 pontos mais críticos que precisam de atenção agora, "
        "considerando meu perfil moderado e objetivos de acumulação + renda passiva. "
        "Para cada ponto, dê uma recomendação concreta e justificada. "
        "Seja direto e objetivo."
    )
    yield from chat_com_agente(
        mensagem_usuario=mensagem,
        historico=[],
        analises=analises,
        macro_dados=macro_dados,
        alertas=alertas,
    )
