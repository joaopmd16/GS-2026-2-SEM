"""Cliente HTTP da API. Único ponto do front que fala com o back-end.

Converte toda falha técnica (API fora do ar, timeout, 4xx/5xx, JSON inválido) em `ErroAPI`
com uma mensagem simples para o cidadão — sem stack trace na tela.
"""
from __future__ import annotations

import os

import requests


class ErroAPI(Exception):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


def _url_padrao() -> str:
    try:
        import streamlit as st
        if "API_URL" in st.secrets:
            return st.secrets["API_URL"]
    except Exception:
        pass
    return os.getenv("API_URL", "http://localhost:8000")


class ClienteAPI:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base = (base_url or _url_padrao()).rstrip("/")
        self.timeout = timeout or float(os.getenv("API_TIMEOUT", "30"))
        self.sessao = requests.Session()

    def _req(self, metodo: str, caminho: str, **kw):
        try:
            r = self.sessao.request(metodo, f"{self.base}{caminho}", timeout=self.timeout, **kw)
        except requests.Timeout:
            raise ErroAPI("O serviço demorou demais para responder. Tente de novo em instantes.")
        except requests.ConnectionError:
            raise ErroAPI("Não conseguimos falar com o serviço agora. Seu relato não foi perdido: "
                          "tente novamente em alguns minutos.")
        if r.status_code == 422:
            raise ErroAPI("Algum campo está inválido. Revise o texto e tente de novo.")
        if r.status_code >= 400:
            detalhe = ""
            try:
                d = r.json().get("detail")
                detalhe = d if isinstance(d, str) and r.status_code < 500 else ""
            except ValueError:
                pass
            raise ErroAPI(detalhe or "O serviço teve um problema. Tente novamente.")
        if r.status_code == 204:
            return None
        try:
            return r.json()
        except ValueError:
            raise ErroAPI("Recebemos uma resposta inesperada do serviço. Tente novamente.")

    # --- endpoints ---
    def saude(self) -> dict:
        return self._req("GET", "/health")

    def listar_ocorrencias(self) -> list[dict]:
        dados = self._req("GET", "/ocorrencias")
        if not isinstance(dados, list):
            raise ErroAPI("Recebemos uma resposta inesperada do serviço.")
        return dados

    def triar(self, descricao: str, bairro: str, lat: float, lon: float) -> dict:
        return self._req("POST", "/triagem", json={"descricao": descricao, "bairro": bairro,
                                                   "latitude": lat, "longitude": lon})

    def confirmar(self, relato: dict, tipo: str, prioridade: str, confianca: float,
                  origem: str) -> dict:
        return self._req("POST", "/ocorrencias", json={
            "relato": relato, "tipo": tipo, "prioridade": prioridade,
            "confianca": confianca, "origem": origem})

    def atualizar_status(self, id_: str, status: str) -> dict:
        return self._req("PATCH", f"/ocorrencias/{id_}", json={"status": status})

    def analisar_foto(self, nome: str, conteudo: bytes, mime: str) -> dict:
        return self._req("POST", "/visao", files={"foto": (nome, conteudo, mime)})

    def conversar(self, mensagem: str, historico: list[dict]) -> dict:
        return self._req("POST", "/chat", json={"mensagem": mensagem,
                                                "historico": historico[-20:]})

    def feedback(self, referencia: str, util: bool, comentario: str = "") -> None:
        self._req("POST", "/feedback", json={"referencia": referencia, "util": util,
                                             "comentario": comentario})
