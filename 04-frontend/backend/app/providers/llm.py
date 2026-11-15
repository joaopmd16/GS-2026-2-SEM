"""Acesso ao LLM. A chave vem SÓ de variável de ambiente; sem chave, o pipeline cai em regras.

Trocar de provedor = implementar `json(sistema, usuario) -> dict`.
"""
from __future__ import annotations

import json
import os
from typing import Protocol

import requests


class ErroLLM(Exception):
    """Falha do provedor (timeout, HTTP, JSON inválido). Nunca vai crua para o cidadão."""


class ProvedorLLM(Protocol):
    def json(self, sistema: str, usuario: str) -> dict: ...


class AnthropicLLM:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, chave: str, modelo: str, timeout: float):
        self.chave, self.modelo, self.timeout = chave, modelo, timeout

    def json(self, sistema: str, usuario: str) -> dict:
        try:
            r = requests.post(
                self.URL,
                headers={"x-api-key": self.chave, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": self.modelo, "max_tokens": 600, "system": sistema,
                      "messages": [{"role": "user", "content": usuario}]},
                timeout=self.timeout,
            )
            r.raise_for_status()
            texto = r.json()["content"][0]["text"]
            ini, fim = texto.find("{"), texto.rfind("}")
            return json.loads(texto[ini:fim + 1])
        except requests.Timeout as e:
            raise ErroLLM("timeout") from e
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            raise ErroLLM(type(e).__name__) from e


def obter_llm() -> ProvedorLLM | None:
    chave = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not chave:
        return None
    return AnthropicLLM(chave, os.getenv("LLM_MODEL", "claude-haiku-5-5"),
                        float(os.getenv("LLM_TIMEOUT", "20")))
