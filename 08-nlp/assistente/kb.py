"""Base de conhecimento: ingestão de documentos, limpeza/normalização,
geração dos 3 corpus (texto puro, perguntas e respostas, conversacional)
e busca BM25 usada como contexto do LLM.

Formatos aceitos: .txt, .md, .html/.htm, .pdf (pypdf), .docx (python-docx, opcional).
"""
from __future__ import annotations

import html as html_lib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

SYSTEM_PROMPT_CORPUS = (
    "Você é o assistente de voz da zeladoria urbana da Prefeitura. "
    "Responda em português do Brasil, com frases curtas e claras."
)

# ---------------------------------------------------------------- leitura

def ler_documento(caminho: Path) -> str:
    ext = caminho.suffix.lower()
    if ext in {".txt", ".md"}:
        return caminho.read_text(encoding="utf-8", errors="ignore")
    if ext in {".html", ".htm"}:
        return html_para_texto(caminho.read_text(encoding="utf-8", errors="ignore"))
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(caminho)).pages)
    if ext == ".docx":
        import docx  # python-docx
        d = docx.Document(str(caminho))
        linhas = []
        for p in d.paragraphs:
            estilo = (p.style.name or "").lower()
            prefixo = "# " if estilo.startswith("heading") or estilo.startswith("título") else ""
            linhas.append(prefixo + p.text)
        return "\n".join(linhas)
    raise ValueError(f"Formato não suportado: {ext}")


def html_para_texto(bruto: str) -> str:
    s = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", bruto)
    s = re.sub(r"(?is)<title>.*?</title>", " ", s)
    s = re.sub(r"(?i)<h[1-3][^>]*>", "\n# ", s)
    s = re.sub(r"(?i)</(p|h[1-6]|li|div|br)\s*>|<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return html_lib.unescape(s)

# ---------------------------------------------------------------- limpeza

RUIDO = [
    re.compile(r"(?i)^p[áa]gina\s+\d+(\s+de\s+\d+)?$"),
    re.compile(r"(?i)^©.*$"),
    re.compile(r"(?i)todos os direitos reservados"),
]


def limpar(texto: str) -> str:
    """Normaliza Unicode (NFC), espaços, quebras de linha e remove ruído
    típico de documentos (rodapés, numeração de página, linhas vazias repetidas)."""
    t = unicodedata.normalize("NFC", texto)
    t = t.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    t = re.sub(r"[​﻿]", "", t)
    t = re.sub(r"[“”]", '"', t)
    t = re.sub(r"[‘’]", "'", t)
    linhas = []
    for ln in t.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if any(r.search(ln) for r in RUIDO):
            continue
        linhas.append(ln)
    t = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", t).strip()

# ---------------------------------------------------------------- estrutura

@dataclass
class Secao:
    servico: str
    topico: str
    texto: str
    fonte: str


ROTULO = re.compile(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç ]{3,30}):\s*(.*)$")


def segmentar(texto: str, fonte: str) -> list[Secao]:
    """Divide o documento em seções (título '# ' ou linha 'Rótulo: texto')."""
    servico = Path(fonte).stem.replace("_", " ")
    secoes: list[Secao] = []
    topico, buffer = "Descrição", []

    def fechar():
        corpo = " ".join(b for b in buffer if b).strip()
        if corpo:
            secoes.append(Secao(servico, topico, corpo, fonte))

    for ln in texto.split("\n"):
        if not ln:
            continue
        m_tit = re.match(r"^#+\s*(.+)$", ln)
        m_rot = ROTULO.match(ln)
        if m_tit:
            titulo = m_tit.group(1).strip()
            if titulo.lower().startswith("serviço:"):
                fechar(); buffer = []
                servico, topico = titulo.split(":", 1)[1].strip(), "Descrição"
            else:
                fechar(); buffer = []
                topico = titulo
        elif m_rot and m_rot.group(1).strip().lower() in {
                "serviço", "o que é", "como solicitar", "prazo", "custo",
                "denúncia", "emergência", "atenção"}:
            rot = m_rot.group(1).strip()
            if rot.lower() == "serviço":
                fechar(); buffer = []
                servico, topico = m_rot.group(2).strip(), "Descrição"
            else:
                fechar(); buffer = [m_rot.group(2)]
                topico = rot.capitalize()
        else:
            buffer.append(ln)
    fechar()
    return secoes

# ---------------------------------------------------------------- corpus

PERGUNTAS = {
    "como solicitar": ["Como eu peço o serviço de {s}?", "Onde eu faço o pedido de {s}?"],
    "prazo": ["Qual é o prazo para {s}?", "Quanto tempo demora {s}?"],
    "custo": ["Quanto custa {s}?"],
    "descrição": ["O que é o serviço de {s}?"],
    "o que é": ["O que é o serviço de {s}?"],
    "emergência": ["E se for uma emergência de {s}?"],
    "responsabilidade": ["De quem é a responsabilidade por {s}?"],
    "acompanhamento": ["Como eu acompanho meu pedido de {s}?"],
}


def _perguntas_para(sec: Secao) -> list[str]:
    s = sec.servico.lower()
    modelos = PERGUNTAS.get(sec.topico.lower(), [f"Fale sobre {sec.topico.lower()} em {{s}}."])
    return [m.format(s=s) for m in modelos]


def gerar_corpus(secoes: list[Secao]) -> dict[str, list[dict]]:
    texto_puro, qa, conversas = [], [], []
    por_servico: dict[str, list[Secao]] = {}
    for sec in secoes:
        por_servico.setdefault(sec.servico, []).append(sec)
        for p in _perguntas_para(sec):
            qa.append({"pergunta": p, "resposta": sec.texto,
                       "servico": sec.servico, "fonte": sec.fonte})

    for servico, lista in por_servico.items():
        texto_puro.append({"text": f"{servico}. " + " ".join(
            f"{s.topico}: {s.texto}" for s in lista), "fonte": lista[0].fonte})
        # conversa de vários turnos com pergunta de continuação
        msgs = [{"role": "system", "content": SYSTEM_PROMPT_CORPUS}]
        for i, sec in enumerate(lista[:4]):
            pergunta = _perguntas_para(sec)[0]
            if i > 0:  # continuação: pronome no lugar do nome do serviço
                pergunta = pergunta.replace(f" de {servico.lower()}", " disso") \
                                   .replace(f" {servico.lower()}", " isso")
            msgs += [{"role": "user", "content": pergunta},
                     {"role": "assistant", "content": sec.texto}]
        conversas.append({"messages": msgs, "servico": servico})

    # exemplos de recusa (fora do escopo) para ensinar limites
    for fora in ["Me receita um remédio para dor de cabeça.",
                 "Qual time vai ganhar o campeonato?",
                 "Como eu entro com um processo contra meu vizinho?"]:
        conversas.append({"messages": [
            {"role": "system", "content": SYSTEM_PROMPT_CORPUS},
            {"role": "user", "content": fora},
            {"role": "assistant", "content": "Desculpe, eu só ajudo com serviços de zeladoria da cidade. "
             "Para isso, procure um profissional ou o órgão responsável."}], "servico": "recusa"})
    return {"texto_puro": texto_puro, "perguntas_respostas": qa, "conversacional": conversas}


def construir(pasta_docs: Path, pasta_saida: Path | None = None) -> tuple[list[Secao], dict]:
    secoes: list[Secao] = []
    for arq in sorted(pasta_docs.iterdir()):
        if arq.suffix.lower() in {".txt", ".md", ".html", ".htm", ".pdf", ".docx"}:
            secoes += segmentar(limpar(ler_documento(arq)), arq.name)
    corpus = gerar_corpus(secoes)
    if pasta_saida:
        pasta_saida.mkdir(parents=True, exist_ok=True)
        for nome, linhas in corpus.items():
            with open(pasta_saida / f"{nome}.jsonl", "w", encoding="utf-8") as f:
                for ln in linhas:
                    f.write(json.dumps(ln, ensure_ascii=False) + "\n")
        with open(pasta_saida / "secoes.json", "w", encoding="utf-8") as f:
            json.dump([asdict(s) for s in secoes], f, ensure_ascii=False, indent=1)
    return secoes, corpus

# ---------------------------------------------------------------- busca

STOP = set("a o as os de da do das dos e é em um uma para por com no na nos nas que eu "
           "meu minha se ou ao à isso disso qual quanto como onde conta quero sou falar faz "
           "tem rua".split())


def tokens(t: str) -> list[str]:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP and len(w) > 1]


class Buscador:
    """BM25 simples (sem dependências) sobre as seções da base."""

    def __init__(self, secoes: list[Secao], k1=1.5, b=0.3):
        self.secoes = secoes
        self.docs = [tokens(f"{s.servico} {s.servico} {s.topico} {s.topico} {s.topico} {s.texto}")
                     for s in secoes]
        self.n = len(self.docs)
        self.avg = sum(map(len, self.docs)) / max(self.n, 1)
        self.df = Counter(w for d in self.docs for w in set(d))
        self.k1, self.b = k1, b

    SINONIMOS = {"tempo": "prazo", "demora": "prazo", "dias": "prazo", "quando": "prazo",
                 "custa": "custo", "pagar": "custo", "pago": "custo", "preco": "custo",
                 "pedir": "solicitar", "peco": "solicitar", "faco": "solicitar",
                 "ligar": "telefone", "buracos": "buraco", "lampada": "iluminacao",
                 "luz": "iluminacao", "poste": "iluminacao", "arvore": "poda",
                 "galho": "poda", "enchente": "alagamento", "lixo": "entulho",
                 "calcadas": "calcada", "protocolo": "acompanhamento",
                 "horario": "atende", "surdo": "libras", "surda": "libras", "levo": "ecoponto",
                 "reforma": "entulho", "denunciar": "denuncia", "conserto": "solicitar",
                 "consertar": "solicitar", "alagada": "alagamento"}

    def buscar(self, consulta: str, k: int = 3) -> list[tuple[float, Secao]]:
        q = tokens(consulta)
        q += [self.SINONIMOS[w] for w in q if w in self.SINONIMOS]
        res = []
        for d, sec in zip(self.docs, self.secoes):
            tf = Counter(d)
            score = 0.0
            for w in q:
                if w not in tf:
                    continue
                idf = math.log(1 + (self.n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                score += idf * tf[w] * (self.k1 + 1) / (
                    tf[w] + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            if score > 0:
                res.append((score, sec))
        return sorted(res, key=lambda x: -x[0])[:k]
