"""Guardrails: prompt injection (direta e indireta), dados pessoais (LGPD),
emergências e verificação de fundamentação (anti-alucinação)."""
import re

from .texto import sem_acento, sentencas, tokens

_INJ = [
    r"ignor\w* (as |todas as |suas |essas |os )?(\w+ )?(instruc|regra|orienta)",
    r"esque\w* (as |suas |todas as )?(instruc|regra)",
    r"(revel|mostr|repit|imprim|exib|diga|conte|vaz)\w* .{0,40}(prompt|instruc\w* (do sistema|inicia|interna)|regras internas)",
    r"system prompt|prompt do sistema|prompt de sistema",
    r"voce (agora )?e (um|uma|o|a) (?!assistente citizentech)",
    r"(aja|finja|atue) como|finja que|faca de conta que",
    r"modo (desenvolvedor|developer|dan|irrestrito)",
    r"jailbreak|ignore previous|disregard",
    r"novas instruc",
]
INJECAO = re.compile("|".join(_INJ))

PII = {
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "telefone": re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}-?\d{4}\b"),
}
PEDIDO_DADO_PESSOAL = re.compile(
    r"\b(cpf|telefone|celular|e-?mail|contato|endereco residencial|nome)\b.{0,60}\b(quem|registr|abri|denunci|autor|cidad|morador)"
    r"|\b(quem|qual (o )?nome).{0,40}(registr|abri|fez|denunci|reclam)")
EMERGENCIA = re.compile(r"desab|deslizamento|desliz|fio\w* (eletric\w* )?caid|risco de vida|incendio|ferid|inclinand|rachando e estalando|estal")


def norm(t: str) -> str:
    return sem_acento(t.lower())


def detectar_injecao(t: str) -> bool:
    return bool(INJECAO.search(norm(t)))


def mascarar_pii(t: str) -> tuple[str, list[str]]:
    achados = []
    for nome, rx in PII.items():
        if rx.search(t):
            achados.append(nome)
            t = rx.sub(f"[{nome.upper()} REMOVIDO]", t)
    return t, achados


def pede_dado_pessoal(t: str) -> bool:
    return bool(PEDIDO_DADO_PESSOAL.search(norm(t)))


def emergencia(t: str) -> bool:
    return bool(EMERGENCIA.search(norm(t)))


def sanitizar_contexto(texto: str) -> tuple[str, bool]:
    """Remove de um trecho recuperado frases com instruções (injeção indireta) e PII."""
    alterado = False
    partes = re.split(r"(?<=[.!?])\s+", texto)
    limpas = []
    for p in partes:
        if detectar_injecao(p):
            alterado = True
            continue
        limpas.append(p)
    out, pii = mascarar_pii(" ".join(limpas))
    return out, alterado or bool(pii)


def suporte(sentenca: str, contexto: str) -> float:
    """Fração dos termos de conteúdo da frase que aparecem no contexto citado."""
    ts = set(tokens(sentenca))
    if not ts:
        return 1.0
    tc = set(tokens(contexto))
    return len(ts & tc) / len(ts)


def verificar_fundamentacao(resposta: str, contextos: dict[int, str], limiar=0.6) -> tuple[str, list[dict]]:
    """Mantém só frases com citação [n] válida e suporte >= limiar no(s) trecho(s) citado(s)."""
    aprovadas, laudo = [], []
    for s in sentencas(resposta):
        refs = [int(x) for x in re.findall(r"\[(\d+)\]", s)]
        refs_validas = [r for r in refs if r in contextos]
        corpo = re.sub(r"\[\d+\]", "", s)
        sup = max((suporte(corpo, contextos[r]) for r in refs_validas), default=0.0)
        ok = bool(refs_validas) and sup >= limiar
        laudo.append({"frase": s, "citacoes": refs, "suporte": round(sup, 2), "aprovada": ok})
        if ok:
            aprovadas.append(s)
    return " ".join(aprovadas), laudo
