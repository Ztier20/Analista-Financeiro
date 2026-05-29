import pandas as pd
import json
from pathlib import Path

def ler_extrato_b3(caminho_arquivo: str) -> dict:
    """
    Lê o Excel exportado pela B3 e retorna a carteira estruturada.
    Processa todas as abas do arquivo.
    """
    carteira = []

    try:
        # Ler todas as abas
        excel_file = pd.ExcelFile(caminho_arquivo)
        abas = excel_file.sheet_names

        print(f"   Processando {len(abas)} aba(s)...\n")

        for aba in abas:
            df = pd.read_excel(caminho_arquivo, sheet_name=aba, engine="openpyxl")

            # Normalizar colunas
            df.columns = [col.strip().upper() for col in df.columns]

            # Remover linhas vazias
            df = df.dropna(how="all")

            for _, row in df.iterrows():
                produto = str(row.get("PRODUTO", "")).strip()
                quantidade = row.get("QUANTIDADE", None)
                preco_medio = row.get("PREÇO MÉDIO", row.get("PRECO MEDIO", None))
                valor_total = row.get("VALOR ATUALIZADO", row.get("VALOR TOTAL", None))

                ativo = classificar_ativo(produto)
                if ativo:
                    ativo["quantidade"] = quantidade
                    ativo["preco_medio"] = preco_medio
                    ativo["valor_total"] = valor_total
                    ativo["aba_origem"] = aba
                    carteira.append(ativo)

    except Exception as e:
        print(f"   ⚠️  Erro ao ler abas: {e}")
        # Fallback: tentar ler primeira aba
        df = pd.read_excel(caminho_arquivo, engine="openpyxl")
        df.columns = [col.strip().upper() for col in df.columns]
        df = df.dropna(how="all")

        for _, row in df.iterrows():
            produto = str(row.get("PRODUTO", "")).strip()
            quantidade = row.get("QUANTIDADE", None)
            preco_medio = row.get("PREÇO MÉDIO", row.get("PRECO MEDIO", None))
            valor_total = row.get("VALOR ATUALIZADO", row.get("VALOR TOTAL", None))

            ativo = classificar_ativo(produto)
            if ativo:
                ativo["quantidade"] = quantidade
                ativo["preco_medio"] = preco_medio
                ativo["valor_total"] = valor_total
                carteira.append(ativo)

    resultado = organizar_por_classe(carteira)

    # Salvar carteira estruturada
    salvar_carteira(resultado)

    return resultado


def classificar_ativo(produto: str) -> dict | None:
    """
    Identifica a classe do ativo pelo nome/código no extrato da B3
    """
    if not produto or produto.upper() == "NAN" or produto == "":
        return None

    partes = produto.split()
    ticker = partes[0].upper() if partes else produto.upper()

    classe = identificar_classe(ticker, produto.upper())

    return {
        "ticker": ticker,
        "descricao": produto,
        "classe": classe
    }


def identificar_classe(ticker: str, descricao: str) -> str:
    """
    Classifica o ativo pela estrutura do ticker e pela descrição
    """
    # ETFs conhecidos — verificar antes de FII para evitar conflito
    etfs_br = [
        "BOVA11", "SMAL11", "IVVB11", "SPXI11", "HASH11",
        "GOLD11", "XFIX11", "NASD11", "ACWI11", "DIVO11",
        "FIND11", "MATB11", "UTIL11", "ISUS11", "TECK11"
    ]
    if ticker in etfs_br:
        return "ETF_BR"

    # FIIs: 4 letras + 11
    if (len(ticker) == 6 and
        ticker[4:] == "11" and
        ticker[:4].isalpha()):
        return "FII"

    # BDRs: 4 letras + 34, 32, 33, 35
    if (len(ticker) == 6 and
        ticker[:4].isalpha() and
        ticker[4:] in ["34", "32", "33", "35"]):
        return "BDR"

    # Ações brasileiras: 4 letras + 1 dígito (3, 4, 5, 6, 7, 8)
    if (len(ticker) == 5 and
        ticker[:4].isalpha() and
        ticker[4].isdigit()):
        return "ACAO_BR"

    # Tesouro Direto
    if "TESOURO" in descricao:
        if "IPCA" in descricao:
            return "TESOURO_IPCA"
        elif "SELIC" in descricao:
            return "TESOURO_SELIC"
        elif "PREFIXADO" in descricao or "PRE" in descricao:
            return "TESOURO_PREFIXADO"
        return "TESOURO"

    # Renda fixa privada
    for tipo in ["CDB", "LCI", "LCA", "CRI", "CRA",
                 "DEBENTURE", "DEBÊNTURE", "FIDC", "LF"]:
        if tipo in descricao:
            return f"RF_{tipo}"

    # Fundos
    if "FDO" in descricao or "FUNDO" in descricao or "FI " in descricao:
        return "FUNDO"

    return "OUTRO"


def organizar_por_classe(carteira: list) -> dict:
    """
    Agrupa os ativos por classe e calcula totais
    """
    resultado = {
        "FII": [],
        "ACAO_BR": [],
        "BDR": [],
        "ETF_BR": [],
        "TESOURO_IPCA": [],
        "TESOURO_SELIC": [],
        "TESOURO_PREFIXADO": [],
        "TESOURO": [],
        "RENDA_FIXA_PRIVADA": [],
        "FUNDO": [],
        "OUTRO": []
    }

    for ativo in carteira:
        classe = ativo["classe"]
        if classe.startswith("RF_"):
            resultado["RENDA_FIXA_PRIVADA"].append(ativo)
        elif classe in resultado:
            resultado[classe].append(ativo)
        else:
            resultado["OUTRO"].append(ativo)

    # Remover classes vazias
    resultado = {k: v for k, v in resultado.items() if v}

    return resultado


def salvar_carteira(carteira: dict):
    """
    Salva a carteira estruturada em data/carteira.json
    """
    caminho = Path("data/carteira.json")
    caminho.parent.mkdir(exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(carteira, f, ensure_ascii=False, indent=2)

    print(f"Carteira salva em {caminho}")


def resumo_carteira(carteira: dict) -> str:
    """
    Gera um resumo textual da carteira para o agente analisar
    """
    linhas = ["=== CARTEIRA ESTRUTURADA ===\n"]

    total_ativos = sum(len(v) for v in carteira.values())
    linhas.append(f"Total de ativos: {total_ativos}\n")

    for classe, ativos in carteira.items():
        linhas.append(f"\n{classe} ({len(ativos)} ativo(s)):")
        for ativo in ativos:
            linha = f"  - {ativo['ticker']}"
            if ativo.get('quantidade'):
                linha += f" | Qtd: {ativo['quantidade']}"
            if ativo.get('valor_total'):
                linha += f" | Valor: R$ {ativo['valor_total']}"
            linhas.append(linha)

    return "\n".join(linhas)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        carteira = ler_extrato_b3(sys.argv[1])
        print(resumo_carteira(carteira))
