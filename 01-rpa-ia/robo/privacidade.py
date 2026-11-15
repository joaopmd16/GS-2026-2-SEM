"""Proteção de dados (LGPD): mascara dados pessoais antes de qualquer saída (e-mail, API, log)."""
import re

PADROES = [
    ("[CPF]", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("[TELEFONE]", re.compile(r"(\(?\b\d{2}\)?\s?)?\b9?\d{4}-?\d{4}\b")),
    ("[PLACA]", re.compile(r"\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b")),
]


def anonimizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    for rotulo, padrao in PADROES:
        texto = padrao.sub(rotulo, texto)
    return texto


def contem_dado_pessoal(texto: str) -> bool:
    return isinstance(texto, str) and any(p.search(texto) for _, p in PADROES)
