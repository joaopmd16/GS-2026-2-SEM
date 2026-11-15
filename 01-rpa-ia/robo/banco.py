"""Tema 4 — SQL (SQLite): persistência, idempotência (não reenvia chamado já encaminhado)
e histórico de execuções (relatório consultável por SQL)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ocorrencias (
  id TEXT PRIMARY KEY, tipo TEXT, origem TEXT, descricao TEXT, confianca REAL,
  latitude REAL, longitude REAL, bairro TEXT, prioridade TEXT, status TEXT,
  criado_em TEXT, orgao TEXT, prazo TEXT, revisao_humana INTEGER DEFAULT 0,
  atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS envios (
  ocorrencia_id TEXT PRIMARY KEY REFERENCES ocorrencias(id),
  destinatario TEXT, arquivo TEXT, enviado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS execucoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, inicio TEXT, fim TEXT,
  lidas INTEGER, validas INTEGER, quarentena INTEGER, encaminhadas INTEGER,
  revisao INTEGER, ja_enviadas INTEGER, falhas INTEGER, fonte_destinos TEXT
);
"""


def conectar(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho)
    con.executescript(ESQUEMA)
    return con


def salvar_ocorrencia(con, o: dict) -> None:
    con.execute(
        """INSERT INTO ocorrencias (id,tipo,origem,descricao,confianca,latitude,longitude,bairro,
             prioridade,status,criado_em,orgao,prazo,revisao_humana)
           VALUES (:id,:tipo,:origem,:descricao,:confianca,:latitude,:longitude,:bairro,
             :prioridade,:status,:criado_em,:orgao,:prazo,:revisao_humana)
           ON CONFLICT(id) DO UPDATE SET tipo=excluded.tipo, prioridade=excluded.prioridade,
             status=excluded.status, orgao=excluded.orgao, prazo=excluded.prazo,
             revisao_humana=excluded.revisao_humana, atualizado_em=CURRENT_TIMESTAMP""", o)


def ja_enviado(con, oid: str) -> bool:
    return con.execute("SELECT 1 FROM envios WHERE ocorrencia_id=?", (oid,)).fetchone() is not None


def registrar_envio(con, oid: str, dest: str, arquivo: str) -> None:
    con.execute("INSERT OR IGNORE INTO envios (ocorrencia_id,destinatario,arquivo) VALUES (?,?,?)",
                (oid, dest, arquivo))


def registrar_execucao(con, r: dict) -> None:
    con.execute("""INSERT INTO execucoes (inicio,fim,lidas,validas,quarentena,encaminhadas,revisao,
                   ja_enviadas,falhas,fonte_destinos) VALUES (:inicio,:fim,:lidas,:validas,
                   :quarentena,:encaminhadas,:revisao,:ja_enviadas,:falhas,:fonte_destinos)""", r)


def resumo_por_bairro(con) -> list[tuple]:
    return con.execute("""SELECT bairro, prioridade, COUNT(*) FROM ocorrencias
                          GROUP BY bairro, prioridade ORDER BY 3 DESC, 1""").fetchall()
