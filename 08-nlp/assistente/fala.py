"""Adaptação do texto para fala (antes do TTS): remove markdown e emojis,
escreve números, datas, horas, valores e siglas de forma pronunciável
e quebra em frases curtas."""
from __future__ import annotations

import re

try:
    from num2words import num2words
except ImportError:  # fallback mínimo
    num2words = None

SIGLAS = {
    "LGPD": "L G P D", "SUS": "SUS", "CEP": "CEP", "CPF": "C P F", "OC": "O C",
    "ODS": "O D S", "IA": "I A", "SP": "São Paulo", "Av.": "Avenida",
    "R.": "Rua", "nº": "número", "n.º": "número", "km": "quilômetros",
}
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF‍️]")


def extenso(n: int, ordinal: bool = False) -> str:
    if num2words:
        return num2words(n, lang="pt_BR", to="ordinal" if ordinal else "cardinal")
    return str(n)


def _feminino(s: str) -> str:
    """Concordância: 'dois horas' -> 'duas horas', 'um hora' -> 'uma hora'."""
    s = re.sub(r"\bdois$", "duas", s)
    s = re.sub(r"\bum$", "uma", s)
    return re.sub(r"entos\b", "entas", s)  # duzentas, trezentas...


def _valor(m: re.Match) -> str:
    reais = int(m.group(1).replace(".", ""))
    cent = int(m.group(2) or 0)
    s = f"{extenso(reais)} {'real' if reais == 1 else 'reais'}"
    if cent:
        s += f" e {extenso(cent)} centavos"
    return s


def _data(m: re.Match) -> str:
    d, mes = int(m.group(1)), int(m.group(2))
    s = f"{'primeiro' if d == 1 else extenso(d)} de {MESES[mes - 1]}"
    if m.group(3):
        s += f" de {extenso(int(m.group(3)))}"
    return s


def _hora(m: re.Match) -> str:
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    s = f"{_feminino(extenso(h))} {'hora' if h == 1 else 'horas'}"
    return s + (f" e {extenso(mi)}" if mi else "")


def _telefone_curto(m: re.Match) -> str:
    # números de serviço (156, 199, 193) são falados dígito a dígito
    return " ".join(extenso(int(c)) for c in m.group(0))


def _protocolo(m: re.Match) -> str:
    return "O C " + " ".join(extenso(int(c)) for c in m.group(1))


def adaptar_para_fala(texto: str, max_palavras: int = 22) -> str:
    t = texto
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)          # links
    t = re.sub(r"(?m)^\s*#+\s*", "", t)                       # títulos
    t = re.sub(r"(?m)^\s*([-*•]|\d+\.)\s+", "", t)            # listas
    t = re.sub(r"[*_`>|]+", "", t)                            # ênfase/tabelas
    t = re.sub(r"https?://\S+", "o endereço no site da Prefeitura", t)
    t = EMOJI.sub("", t)
    t = re.sub(r"\bOC-(\d+)\b", _protocolo, t)
    t = re.sub(r"R\$\s?([\d.]+)(?:,(\d{2}))?", _valor, t)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", _data, t)
    t = re.sub(r"\b(\d{1,2})h(\d{2})?\b", _hora, t)
    t = re.sub(r"\b(15[0-9]|19[0-9])\b", _telefone_curto, t)
    t = re.sub(r"\b(\d+)(º|ª)", lambda m: extenso(int(m.group(1)), True), t)
    t = re.sub(r"\b(\d+)%", lambda m: f"{extenso(int(m.group(1)))} por cento", t)
    t = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b", lambda m: extenso(int(m.group(0).replace(".", ""))), t)
    t = re.sub(r"\b(\d+)(?=\s+(horas?|semanas?|vezes|pessoas|ruas|árvores|lâmpadas)\b)",
               lambda m: _feminino(extenso(int(m.group(1)))), t)
    t = re.sub(r"\b\d+\b", lambda m: extenso(int(m.group(0))), t)
    for sig, fala in SIGLAS.items():
        t = re.sub(rf"(?<!\w){re.escape(sig)}(?!\w)", fala, t)
    t = t.replace(";", ".").replace(":", ",")
    t = re.sub(r"\s+", " ", t).strip()

    # frases curtas: quebra frases longas em vírgulas
    frases = []
    for f in re.split(r"(?<=[.!?])\s+", t):
        palavras = f.split()
        while len(palavras) > max_palavras:
            corte = next((i for i in range(max_palavras, 5, -1)
                          if palavras[i - 1].endswith(",")), max_palavras)
            frases.append(" ".join(palavras[:corte]).rstrip(",") + ".")
            palavras = palavras[corte:]
        if palavras:
            frases.append(" ".join(palavras))
    return " ".join(frases)
