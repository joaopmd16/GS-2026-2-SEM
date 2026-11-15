"""Normalização e tokenização em português (sem dependências externas)."""
import re
import unicodedata


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


STOP = {sem_acento(s) for s in """a o e é de da do das dos em no na nos nas um uma uns umas para por com sem que se
ao aos à às ou como mais mas meu minha seu sua eu você voce vc qual quais quando onde
quem isso esse essa este esta ele ela eles elas me te lhe já ja foi ser tem ter há
pra pro tá ta sobre entre também tambem muito pode posso preciso quero fazer faz
oi ola olá favor obrigado então entao""".split()}


def radical(p: str) -> str:
    """Stemming leve: corta sufixos comuns de plural/gênero/verbo."""
    for suf in ("mente", "coes", "cao", "oes", "ais", "eis", "res", "ar", "er", "ir", "as", "os", "es", "a", "o", "s"):
        if len(p) > len(suf) + 3 and p.endswith(suf):
            return p[: -len(suf)]
    return p


def tokens(t: str, stem: bool = True) -> list[str]:
    ps = re.findall(r"[a-z0-9]+", sem_acento(t.lower()))
    ps = [p for p in ps if p not in STOP and len(p) > 1]
    return [radical(p) for p in ps] if stem else ps


def sentencas(t: str) -> list[str]:
    partes = re.split(r"(?<=[.!?])\s+|\n+", t)
    return [p.strip(" -") for p in partes if len(p.strip()) > 15]


# Expansão de consulta com sinônimos do domínio (vocabulário do cidadão -> vocabulário da base)
SINONIMOS = {
    "conserto": "reparo", "consertar": "reparo manutencao", "peco": "pedir solicitar", "pedir": "solicitar",
    "ligar": "ligacao telefonica telefone", "surdo": "surdas deficiencia auditiva", "quer dizer": "significado",
    "significa": "significado", "demora": "prazo", "tapar": "tapa-buraco reparo", "protocolo venceu": "prazo ouvidoria",
}


def expandir_consulta(q: str) -> str:
    qn = sem_acento(q.lower())
    extra = [v for k, v in SINONIMOS.items() if re.search(rf"\b{k}\b", qn)]
    return q + (" " + " ".join(extra) if extra else "")
