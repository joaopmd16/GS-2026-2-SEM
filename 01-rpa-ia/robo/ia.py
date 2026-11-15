"""IA (NLP por regras + aproveitamento do modelo de Visão): classifica tipo e prioridade.

- Se a ocorrência vem da Visão Computacional (09) com confiança >= 0.6, confia no tipo do modelo.
- Senão, classifica o texto por palavras-chave normalizadas (sem acento) com pontuação.
- Prioridade: regras de risco/vulnerabilidade (acessibilidade, escola, hospital, acidente...).
- Baixa confiança -> marcado para REVISÃO HUMANA (o robô não decide sozinho).
"""
from __future__ import annotations

import re
import unicodedata

PALAVRAS_TIPO = {
    "buraco": ["buraco", "cratera", "asfalto", "afundamento", "afundou", "pista", "via esburacada",
               "pneu", "valeta"],
    "fissura": ["fissura", "rachadura", "trinca", "racha", "rachado", "trincado", "muro", "parede",
                "viaduto", "calcada rachada"],
    "alerta_sonoro": ["sirene", "alarme", "barulho", "som", "estrondo", "explosao", "buzina",
                      "campainha", "ruido"],
}
RISCO_ALTO = ["acidente", "crianca", "escola", "hospital", "cadeirante", "cadeira de rodas",
              "idoso", "desabamento", "desabar", "risco", "perigo", "profundo", "enorme",
              "caiu", "ferido", "surdo", "deficiente", "urgente", "explosao", "desmoronar"]
RISCO_BAIXO = ["pequeno", "pequena", "leve", "superficial", "estetico", "fina"]

LIMIAR_VISAO = 0.6
LIMIAR_REVISAO = 0.5


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    return re.sub(r"\s+", " ", "".join(c for c in t if not unicodedata.combining(c)))


def classificar_tipo(descricao: str, tipo_atual: str = "", origem: str = "",
                     confianca: float = 0.0) -> tuple[str, float]:
    if tipo_atual and origem == "visao" and confianca >= LIMIAR_VISAO:
        return tipo_atual, float(confianca)
    txt = normalizar(descricao)
    pontos = {t: sum(1 for p in ps if p in txt) for t, ps in PALAVRAS_TIPO.items()}
    melhor = max(pontos, key=pontos.get)
    total = sum(pontos.values())
    if total == 0:
        # sem pista no texto: mantém o tipo do modelo com a confiança dele, ou "outro" incerto
        return (tipo_atual, float(confianca)) if tipo_atual else ("outro", 0.3)
    conf = pontos[melhor] / total
    if list(pontos.values()).count(pontos[melhor]) > 1:  # empate
        conf = 0.4
    return melhor, round(min(0.95, 0.5 + 0.45 * conf), 2)


def classificar_prioridade(descricao: str, tipo: str) -> str:
    txt = normalizar(descricao)
    if any(p in txt for p in RISCO_ALTO):
        return "alta"
    if any(p in txt for p in RISCO_BAIXO):
        return "baixa"
    return "media" if tipo in {"buraco", "fissura", "alerta_sonoro"} else "baixa"


def classificar(row: dict) -> dict:
    tipo, conf = classificar_tipo(row.get("descricao", ""), row.get("tipo", ""),
                                  row.get("origem", ""), float(row.get("confianca") or 0))
    prio = classificar_prioridade(row.get("descricao", ""), tipo)
    return {"tipo_ia": tipo, "confianca_ia": conf, "prioridade_ia": prio,
            "revisao_humana": conf < LIMIAR_REVISAO}
