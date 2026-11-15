"""Tema 1 — Pandas: leitura, limpeza e validação das ocorrências (contrato do CONTEXTO.md)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger("robo")

COLUNAS = ["id", "tipo", "origem", "descricao", "confianca", "latitude", "longitude",
           "bairro", "prioridade", "status", "criado_em"]
TIPOS = {"fissura", "buraco", "alerta_sonoro", "outro"}
ORIGENS = {"visao", "iot", "chat", "rpa"}


def ler_ocorrencias(caminho: Path) -> pd.DataFrame:
    """Lê o CSV. Arquivo ausente/corrompido -> DataFrame vazio + log (caminho seguro)."""
    try:
        df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    except FileNotFoundError:
        log.error("Arquivo de entrada não encontrado: %s — execução segue sem ocorrências", caminho)
        return pd.DataFrame(columns=COLUNAS)
    except (pd.errors.ParserError, UnicodeDecodeError, pd.errors.EmptyDataError) as e:
        log.error("Arquivo de entrada ilegível (%s): %s", caminho, e)
        return pd.DataFrame(columns=COLUNAS)
    for c in COLUNAS:
        if c not in df.columns:
            log.warning("Coluna ausente '%s' — preenchida vazia", c)
            df[c] = ""
    return df[COLUNAS]


def validar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa registros válidos e inválidos (quarentena, com motivo)."""
    df = df.copy()
    for c in COLUNAS:
        df[c] = df[c].astype(str).str.strip()
    df["tipo"] = df["tipo"].str.lower()
    df["origem"] = df["origem"].str.lower()
    df["confianca"] = pd.to_numeric(df["confianca"].str.replace(",", "."), errors="coerce").fillna(0.0)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["criado_dt"] = pd.to_datetime(df["criado_em"], errors="coerce", format="ISO8601")

    motivos = pd.Series("", index=df.index)

    def marca(mask, msg):
        motivos.loc[mask] = motivos.loc[mask] + msg + "; "

    marca(~df["id"].str.match(r"^OC-\d{4,}$"), "id inválido")
    marca(df["id"].duplicated(keep="first"), "id duplicado")
    marca(df["descricao"].str.len() < 5, "descrição vazia/curta")
    marca(~df["latitude"].between(-90, 90) | ~df["longitude"].between(-180, 180), "coordenada inválida")
    marca(df["criado_dt"].isna(), "data inválida")
    marca(~df["origem"].isin(ORIGENS), "origem inválida")
    marca(~df["confianca"].between(0, 1), "confiança fora de [0,1]")

    df["motivo_invalido"] = motivos.str.rstrip("; ")
    invalidos = df[df["motivo_invalido"] != ""]
    validos = df[df["motivo_invalido"] == ""].drop(columns="motivo_invalido")
    # tipo desconhecido não invalida: a IA reclassifica
    validos.loc[~validos["tipo"].isin(TIPOS), "tipo"] = ""
    log.info("Validação: %d válidas, %d em quarentena", len(validos), len(invalidos))
    return validos, invalidos
