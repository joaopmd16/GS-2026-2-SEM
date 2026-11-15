"""Utilidades: log, retry com espera exponencial e configuração por variáveis de ambiente."""
from __future__ import annotations

import functools
import logging
import os
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # pasta 01-rpa-ia
SAIDA = BASE / "saida"


def carregar_env(arquivo: Path = BASE / ".env") -> None:
    """Lê um .env simples (CHAVE=valor) sem dependências externas. Nunca versionado."""
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def configurar_log(pasta: Path = SAIDA) -> logging.Logger:
    pasta.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("robo")
    if not log.handlers:
        log.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(module)s | %(message)s")
        fh = logging.FileHandler(pasta / "robo.log", encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(fh)
        log.addHandler(sh)
    return log


def retry(tentativas: int = 3, espera: float = 1.0, excecoes: tuple = (Exception,)):
    """Repete a função com espera exponencial (1s, 2s, 4s...). Relança na última falha."""

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            log = logging.getLogger("robo")
            for i in range(1, tentativas + 1):
                try:
                    return fn(*a, **kw)
                except excecoes as e:
                    if i == tentativas:
                        log.error("%s falhou após %d tentativas: %s", fn.__name__, i, e)
                        raise
                    pausa = espera * 2 ** (i - 1)
                    log.warning("%s falhou (tentativa %d/%d): %s — nova tentativa em %.1fs",
                                fn.__name__, i, tentativas, e, pausa)
                    time.sleep(pausa)

        return wrapper

    return deco
