"""
Histórico de Scores — SQLite
Persiste scores de cada análise para acompanhar evolução no tempo
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


DB_PATH = Path("data/historico.db")


def _conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria as tabelas se não existirem"""
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                data      TEXT    NOT NULL,
                ticker    TEXT    NOT NULL,
                classe    TEXT    NOT NULL,
                score     REAL,
                categoria TEXT,
                recomendacao TEXT,
                valor_total  REAL,
                selic     REAL,
                ipca      REAL,
                cdi       REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_ticker ON scores(ticker)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_data   ON scores(data)")
        conn.commit()


def salvar_analise(analises: Dict, macro_dados: Dict):
    """
    Persiste scores de uma análise completa no banco

    Args:
        analises: Dict {classe: [{ticker, score, ...}]} vindo do dashboard
        macro_dados: Dict com selic, ipca_12m, cdi
    """
    criar_tabelas()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selic = macro_dados.get("selic")
    ipca  = macro_dados.get("ipca_12m")
    cdi   = macro_dados.get("cdi")

    rows = []
    for classe, ativos_lista in analises.items():
        for ativo in ativos_lista:
            score_info = ativo.get("score", {})
            score = score_info.get("score") if isinstance(score_info, dict) else score_info
            try:
                score = float(score) if score not in (None, "N/A") else None
            except (ValueError, TypeError):
                score = None

            rows.append((
                agora,
                ativo.get("ticker"),
                classe,
                score,
                score_info.get("categoria") if isinstance(score_info, dict) else None,
                None,  # recomendacao (futuramente)
                ativo.get("valor", 0),
                selic, ipca, cdi,
            ))

    with _conectar() as conn:
        conn.executemany("""
            INSERT INTO scores
              (data, ticker, classe, score, categoria, recomendacao, valor_total, selic, ipca, cdi)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, rows)
        conn.commit()

    return len(rows)


def buscar_historico_ticker(ticker: str, dias: int = 90) -> pd.DataFrame:
    """Retorna histórico de score de um ticker nos últimos N dias"""
    criar_tabelas()
    with _conectar() as conn:
        df = pd.read_sql_query("""
            SELECT data, ticker, classe, score, categoria, selic, ipca, cdi
            FROM scores
            WHERE ticker = ?
              AND data >= datetime('now', ?)
            ORDER BY data ASC
        """, conn, params=(ticker, f"-{dias} days"))
    return df


def buscar_historico_carteira(dias: int = 90) -> pd.DataFrame:
    """Retorna histórico de todos os ativos nos últimos N dias"""
    criar_tabelas()
    with _conectar() as conn:
        df = pd.read_sql_query("""
            SELECT data, ticker, classe, score, categoria, selic, ipca, cdi
            FROM scores
            WHERE data >= datetime('now', ?)
            ORDER BY data ASC
        """, conn, params=(f"-{dias} days",))
    return df


def buscar_ultima_analise() -> pd.DataFrame:
    """Retorna os scores da análise mais recente"""
    criar_tabelas()
    with _conectar() as conn:
        df = pd.read_sql_query("""
            SELECT ticker, classe, score, categoria, data
            FROM scores
            WHERE data = (SELECT MAX(data) FROM scores)
            ORDER BY score DESC
        """, conn)
    return df


def buscar_penultima_analise() -> pd.DataFrame:
    """Retorna os scores da segunda análise mais recente"""
    criar_tabelas()
    with _conectar() as conn:
        df = pd.read_sql_query("""
            SELECT ticker, classe, score, categoria, data
            FROM scores
            WHERE data = (
                SELECT DISTINCT data FROM scores
                ORDER BY data DESC
                LIMIT 1 OFFSET 1
            )
            ORDER BY score DESC
        """, conn)
    return df


def calcular_variacao_scores() -> pd.DataFrame:
    """
    Compara última análise com a anterior
    Retorna DataFrame com variação de score por ticker
    """
    ultima    = buscar_ultima_analise()
    penultima = buscar_penultima_analise()

    if ultima.empty or penultima.empty:
        return pd.DataFrame()

    merged = ultima.merge(
        penultima[["ticker", "score", "data"]],
        on="ticker",
        suffixes=("_atual", "_anterior"),
        how="left"
    )
    merged["variacao"] = merged["score_atual"] - merged["score_anterior"]
    merged["variacao_pct"] = (merged["variacao"] / merged["score_anterior"].abs() * 100).round(1)
    return merged.sort_values("variacao")


def contar_analises() -> int:
    """Conta quantas análises foram salvas"""
    criar_tabelas()
    with _conectar() as conn:
        row = conn.execute("SELECT COUNT(DISTINCT data) FROM scores").fetchone()
        return row[0] if row else 0
