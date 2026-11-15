"""Ingestão e chunking da base de conhecimento + ocorrências.

Estratégias:
- "estrutural" (padrão): um chunk por seção H2 do documento, prefixado com o título
  do documento e da seção (preserva metadados e contexto); seções longas são
  divididas em janelas de `max_chars` com `overlap`, cortando em fim de frase.
- "fixo": janelas de tamanho fixo sobre o texto corrido, ignorando a estrutura.
"""
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
KB_DIR = BASE / "kb"
OCORRENCIAS_CSV = BASE / "dados" / "ocorrencias_exemplo.csv"
OCORRENCIAS_PROJETO = BASE.parent / "dados" / "ocorrencias.csv"
CAMPOS_PUBLICOS = ["id", "tipo", "origem", "descricao", "bairro", "prioridade", "status", "criado_em"]


@dataclass
class Chunk:
    id: str
    texto: str
    meta: dict = field(default_factory=dict)


def ler_doc(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta, corpo = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha:
                k, v = linha.split(":", 1)
                meta[k.strip()] = v.strip()
        corpo = m.group(2)
    meta["arquivo"] = path.name
    return meta, corpo


def janelas(texto: str, max_chars: int, overlap: int) -> list[str]:
    if len(texto) <= max_chars:
        return [texto]
    out, i = [], 0
    while i < len(texto):
        fim = min(len(texto), i + max_chars)
        corte = texto.rfind(". ", i, fim)
        if fim < len(texto) and corte > i + max_chars // 2:
            fim = corte + 1
        out.append(texto[i:fim].strip())
        if fim >= len(texto):
            break
        i = max(fim - overlap, i + 1)
    return out


def chunk_estrutural(meta, corpo, max_chars=700, overlap=120) -> list[Chunk]:
    chunks = []
    for s in re.split(r"\n(?=## )", corpo):
        linhas = [l for l in s.strip().splitlines() if not l.startswith("# ")]
        if not linhas:
            continue
        if linhas[0].startswith("## "):
            secao, resto = linhas[0][3:].strip(), linhas[1:]
        else:
            secao, resto = "Introdução", linhas
        corpo_sec = " ".join(l.strip() for l in resto if l.strip())
        if not corpo_sec:
            continue
        for j, parte in enumerate(janelas(corpo_sec, max_chars, overlap)):
            cid = f"{meta['arquivo']}#{secao}" + (f"/{j}" if j else "")
            chunks.append(Chunk(cid, f"{meta.get('titulo', '')} — {secao}: {parte}", {**meta, "secao": secao}))
    return chunks


def chunk_fixo(meta, corpo, max_chars=300, overlap=50) -> list[Chunk]:
    texto = re.sub(r"\s+", " ", re.sub(r"#+ ", "", corpo)).strip()
    return [Chunk(f"{meta['arquivo']}@{j}", p, {**meta, "secao": f"janela {j}"})
            for j, p in enumerate(janelas(texto, max_chars, overlap))]


def carregar_ocorrencias(path: Path | None = None) -> list[dict]:
    path = path or (OCORRENCIAS_CSV if OCORRENCIAS_CSV.exists() else OCORRENCIAS_PROJETO)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def chunks_ocorrencias(ocs: list[dict]) -> list[Chunk]:
    """Só campos públicos entram no índice (minimização LGPD: sem contato nem coordenadas)."""
    out = []
    for o in ocs:
        pub = {k: (o.get(k) or "") for k in CAMPOS_PUBLICOS}
        texto = (f"Ocorrência {pub['id']}: {pub['tipo']} no bairro {pub['bairro']}. "
                 f"Descrição: {pub['descricao']}. Status: {pub['status']}. Prioridade: {pub['prioridade']}. "
                 f"Registrada em {pub['criado_em'][:10]} via {pub['origem']}.")
        out.append(Chunk(f"ocorrencia#{pub['id']}", texto,
                         {"titulo": f"Ocorrência {pub['id']}", "fonte": "Base de ocorrências CitizenTech",
                          "url": "dados/ocorrencias_exemplo.csv", "arquivo": "ocorrencias", **pub,
                          "secao": pub["id"]}))
    return out


def construir_corpus(estrategia="estrutural", max_chars=None, overlap=None, kb_dir: Path = KB_DIR,
                     incluir_ocorrencias=True, ocorrencias: list[dict] | None = None) -> list[Chunk]:
    fn = chunk_estrutural if estrategia == "estrutural" else chunk_fixo
    kw = {}
    if max_chars:
        kw["max_chars"] = max_chars
    if overlap is not None:
        kw["overlap"] = overlap
    chunks = []
    for p in sorted(Path(kb_dir).glob("*.md")):
        meta, corpo = ler_doc(p)
        chunks += fn(meta, corpo, **kw)
    if incluir_ocorrencias:
        chunks += chunks_ocorrencias(ocorrencias if ocorrencias is not None else carregar_ocorrencias())
    return chunks
