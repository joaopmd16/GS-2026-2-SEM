"""Recuperadores: BM25 (lexical), TF-IDF de n-gramas de caracteres (vetorial esparso,
proxy offline de embeddings, robusto a erros de digitação e flexões) e híbrido por
Reciprocal Rank Fusion (RRF)."""
import math
import re
from collections import Counter

from .texto import sem_acento, tokens


class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [tokens(c.texto) for c in chunks]
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def scores(self, q):
        qt = tokens(q)
        out = []
        for tf, d in zip(self.tf, self.docs):
            s = 0.0
            for t in qt:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avgdl))
            out.append(s)
        return out


def ngramas(t, ns=(3, 4, 5)):
    t = " " + re.sub(r"\s+", " ", sem_acento(t.lower())) + " "
    return Counter(t[i:i + n] for n in ns for i in range(len(t) - n + 1))


class TfidfChar:
    def __init__(self, chunks):
        vs = [ngramas(c.texto) for c in chunks]
        n = len(vs)
        df = Counter(g for v in vs for g in v)
        self.idf = {g: math.log((1 + n) / (1 + f)) + 1 for g, f in df.items()}
        self.vecs = [self._pesar(v) for v in vs]

    def _pesar(self, v):
        w = {g: (1 + math.log(f)) * self.idf.get(g, 0) for g, f in v.items()}
        norm = math.sqrt(sum(x * x for x in w.values())) or 1
        return {g: x / norm for g, x in w.items() if x}

    def scores(self, q):
        qv = self._pesar(ngramas(q))
        return [sum(x * d.get(g, 0) for g, x in qv.items()) for d in self.vecs]


class Retriever:
    def __init__(self, chunks, modo="hibrido", rrf_k=60):
        self.chunks, self.modo, self.rrf_k = chunks, modo, rrf_k
        self.bm25 = BM25(chunks)
        self.tfidf = TfidfChar(chunks)

    def buscar(self, q, k=4, filtro=None):
        idx = [i for i, c in enumerate(self.chunks) if not filtro or filtro(c)]
        sb, sv = self.bm25.scores(q), self.tfidf.scores(q)
        if self.modo == "bm25":
            ordem = sorted(idx, key=lambda i: -sb[i])
        elif self.modo == "vetorial":
            ordem = sorted(idx, key=lambda i: -sv[i])
        else:
            rb = {i: r for r, i in enumerate(sorted(idx, key=lambda i: -sb[i]))}
            rv = {i: r for r, i in enumerate(sorted(idx, key=lambda i: -sv[i]))}
            ordem = sorted(idx, key=lambda i: -(1 / (self.rrf_k + rb[i]) + 1 / (self.rrf_k + rv[i])))
        return [(self.chunks[i], {"bm25": round(sb[i], 3), "vetorial": round(sv[i], 3)}) for i in ordem[:k]]
