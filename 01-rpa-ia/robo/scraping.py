"""Tema 2 — Web scraping (requests + BeautifulSoup): descobre para qual órgão/e-mail e com
qual prazo cada tipo de ocorrência deve ser encaminhado, lendo a página de serviços da prefeitura.

Por padrão lê a página simulada `dados_teste/portal_prefeitura.html` (dados sintéticos).
Pode apontar para uma URL via PORTAL_URL. Se o site estiver fora do ar ou o HTML mudar,
usa a tabela padrão (caminho seguro) e registra no log.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .util import BASE, retry

log = logging.getLogger("robo")

PADRAO = {
    "buraco": {"orgao": "Central de Zeladoria (padrão)", "email": "zeladoria@prefeitura.exemplo", "prazo_dias": 5},
    "fissura": {"orgao": "Central de Zeladoria (padrão)", "email": "zeladoria@prefeitura.exemplo", "prazo_dias": 5},
    "alerta_sonoro": {"orgao": "Central de Zeladoria (padrão)", "email": "zeladoria@prefeitura.exemplo", "prazo_dias": 2},
    "outro": {"orgao": "Central de Zeladoria (padrão)", "email": "zeladoria@prefeitura.exemplo", "prazo_dias": 10},
}
PAGINA_LOCAL = BASE / "dados_teste" / "portal_prefeitura.html"


@retry(tentativas=3, espera=0.5, excecoes=(requests.RequestException,))
def _baixar(url: str) -> str:
    r = requests.get(url, timeout=5, headers={"User-Agent": "CitizenTech-RPA-academico/1.0"})
    r.raise_for_status()
    return r.text


def parse_tabela(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    tabela = soup.find("table", id="encaminhamento")
    if tabela is None:
        raise ValueError("tabela #encaminhamento não encontrada (layout mudou?)")
    destinos = {}
    for tr in tabela.select("tbody tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(tds) < 4:
            continue
        tipo, orgao, email, prazo = tds[:4]
        try:
            destinos[tipo.lower()] = {"orgao": orgao, "email": email, "prazo_dias": int(prazo)}
        except ValueError:
            log.warning("Linha ignorada no scraping (prazo inválido): %s", tds)
    if not destinos:
        raise ValueError("tabela sem linhas válidas")
    return destinos


def obter_destinos(url: str | None = None, arquivo: Path = PAGINA_LOCAL) -> tuple[dict, str]:
    """Retorna (destinos, fonte). Nunca levanta exceção: cai na tabela padrão."""
    url = url or os.getenv("PORTAL_URL")
    try:
        if url:
            html, fonte = _baixar(url), url
        else:
            html, fonte = Path(arquivo).read_text(encoding="utf-8"), str(Path(arquivo).name)
        destinos = parse_tabela(html)
        log.info("Scraping OK (%s): %d tipos mapeados", fonte, len(destinos))
        return {**PADRAO, **destinos}, fonte
    except Exception as e:  # site fora do ar, arquivo ausente, layout alterado
        log.error("Scraping falhou (%s) — usando tabela padrão", e)
        return dict(PADRAO), "padrao"
