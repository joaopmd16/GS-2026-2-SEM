"""Tema 3 — Consumo de API REST pública e gratuita (BrasilAPI, feriados nacionais).

Usada para calcular o prazo (SLA) do chamado em DIAS ÚTEIS. Só envia o ano à API — nenhum
dado pessoal sai do robô. Tem timeout, retry com espera, cache local e caminho seguro
(sem feriados) se a API falhar ou ROBO_OFFLINE=1.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta

import requests

from .util import SAIDA, retry

log = logging.getLogger("robo")
URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"


@retry(tentativas=3, espera=1.0, excecoes=(requests.RequestException, ValueError))
def _consultar(ano: int) -> list:
    r = requests.get(URL.format(ano=ano), timeout=5)
    r.raise_for_status()
    dados = r.json()
    if not isinstance(dados, list) or not all("date" in d for d in dados):
        raise ValueError("resposta inesperada da API")
    return dados


def feriados(ano: int) -> set[date]:
    cache = SAIDA / f"cache_feriados_{ano}.json"
    if cache.exists():
        return {date.fromisoformat(d) for d in json.loads(cache.read_text())}
    if os.getenv("ROBO_OFFLINE") == "1":
        log.warning("Modo offline: prazos calculados sem feriados")
        return set()
    try:
        datas = sorted(d["date"] for d in _consultar(ano))
        SAIDA.mkdir(exist_ok=True)
        cache.write_text(json.dumps(datas))
        log.info("API de feriados OK: %d feriados em %d", len(datas), ano)
        return {date.fromisoformat(d) for d in datas}
    except Exception as e:
        log.error("API de feriados indisponível (%s) — prazo sem feriados", e)
        return set()


def somar_dias_uteis(inicio: date, dias: int, fer: set[date] | None = None) -> date:
    fer = fer if fer is not None else feriados(inicio.year)
    d = inicio
    while dias > 0:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in fer:
            dias -= 1
    return d
