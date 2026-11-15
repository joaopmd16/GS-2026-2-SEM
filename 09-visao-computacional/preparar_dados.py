"""Etapa 1 — Seleção e preparação dos dados (Concrete Crack Images for Classification).

Base: Özgenel, Ç.F. (2019) Mendeley Data v2, DOI 10.17632/5y9wdsg2zt.2
40.000 recortes 227x227 RGB (20k Positive = com fissura, 20k Negative = sem fissura),
gerados a partir de 458 fotos de alta resolução de prédios do campus METU.

Vazamento entre conjuntos: o dataset não informa a foto de origem de cada recorte,
mas os arquivos são numerados sequencialmente na ordem de geração (recortes vizinhos
saem da mesma foto). Por isso o split é feito por BLOCOS de numeração contígua
(GRUPO arquivos por bloco) e cada bloco inteiro vai para um único conjunto — nunca
recortes vizinhos em treino e teste. É uma aproximação documentada no README.

Uso:
    python preparar_dados.py --origem <pasta com Positive/ e Negative/> --por-classe 3000
Gera dados/split.csv (caminho, rotulo, conjunto, bloco).
"""
import argparse
import csv
import random
from pathlib import Path

GRUPO = 100  # tamanho do bloco de numeração contígua (~1 foto original ≈ 87 recortes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", required=True)
    ap.add_argument("--por-classe", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    origem = Path(a.origem)
    linhas = []
    for classe, rotulo in (("Negative", 0), ("Positive", 1)):
        arqs = sorted((origem / classe).glob("*.jpg"))
        blocos = {}
        for p in arqs:
            idx = int(p.stem.split("_")[0])
            blocos.setdefault(idx // GRUPO, []).append(p)
        ids = sorted(blocos)
        rnd.shuffle(ids)
        n = len(ids)
        cortes = {"treino": ids[: int(0.7 * n)], "validacao": ids[int(0.7 * n): int(0.85 * n)],
                  "teste": ids[int(0.85 * n):]}
        for conj, bl in cortes.items():
            pool = [(p, b) for b in bl for p in blocos[b]]
            k = int(a.por_classe * {"treino": 0.7, "validacao": 0.15, "teste": 0.15}[conj])
            for p, b in rnd.sample(pool, min(k, len(pool))):
                linhas.append((p.relative_to(origem).as_posix(), rotulo, conj, f"{classe[0]}{b}"))
    out = Path(__file__).parent / "dados" / "split.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["caminho", "rotulo", "conjunto", "bloco"])
        w.writerows(linhas)
    # checagem de vazamento: nenhum bloco em mais de um conjunto
    por_bloco = {}
    for _, _, c, b in linhas:
        por_bloco.setdefault(b, set()).add(c)
    assert all(len(s) == 1 for s in por_bloco.values()), "vazamento entre conjuntos!"
    from collections import Counter
    print(Counter((c, r) for _, r, c, _ in linhas))
    print("OK — sem blocos compartilhados entre conjuntos ->", out)


if __name__ == "__main__":
    main()
