"""Etapas 4 e 5 — Demonstração integrada + medição de desempenho.

    python demo_monitoramento.py --origem <pasta do dataset>

1. Monta uma "ronda" de 20 quadros 681x454 (mosaicos 3x2 de recortes do CONJUNTO DE TESTE,
   com trechos com e sem fissura, alguns com sombra/baixa luz simuladas) e grava como
   vídeo — simula a câmera de um agente/veículo de zeladoria.
2. Processa o vídeo com visao.processar_sequencia (vídeo anotado + ocorrências).
3. Benchmark: latência média e FPS (recorte único 227x227 e quadro 681x454 = 6 janelas),
   com e sem Grad-CAM, informando o equipamento.
Saídas em resultados/: ronda_original.mp4, ronda_anotada.mp4, quadros_exemplo.png,
ocorrencias_demo.json, desempenho.json
"""
import argparse
import csv
import json
import platform
import random
import time
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageEnhance

import visao

RAIZ = Path(__file__).parent
RES = RAIZ / "resultados"
BAIRROS = [("Sé", -23.5503, -46.6340), ("Liberdade", -23.5587, -46.6350), ("Bela Vista", -23.5614, -46.6474)]


def montar_quadros(origem, n=20, seed=7):
    rnd = random.Random(seed)
    pos, neg = [], []
    with open(RAIZ / "dados" / "split.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["conjunto"] == "teste":
                (pos if r["rotulo"] == "1" else neg).append(Path(origem) / r["caminho"])
    quadros, verdade = [], []
    for i in range(n):
        k = 0 if i % 4 in (0, 1) else rnd.choice([1, 2, 3])  # metade dos quadros sem fissura
        esc = rnd.sample(pos, k) + rnd.sample(neg, 6 - k)
        rnd.shuffle(esc)
        tiles = [Image.open(p).convert("RGB") for p in esc]
        q = Image.new("RGB", (681, 454))
        for j, t in enumerate(tiles):
            q.paste(t, ((j % 3) * 227, (j // 3) * 227))
        if i % 5 == 4:   # interferência: pouca luz / sombra
            q = ImageEnhance.Brightness(q).enhance(0.45)
        quadros.append(np.asarray(q)); verdade.append(k > 0)
    return quadros, verdade


def bench(fn, reps):
    fn()  # aquecimento
    t = []
    for _ in range(reps):
        t0 = time.perf_counter(); fn(); t.append(time.perf_counter() - t0)
    ms = float(np.mean(t) * 1000)
    return {"latencia_media_ms": round(ms, 1), "p95_ms": round(float(np.percentile(t, 95) * 1000), 1),
            "fps": round(1000 / ms, 1)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--origem", required=True); a = ap.parse_args()
    RES.mkdir(exist_ok=True)
    quadros, verdade = montar_quadros(a.origem)
    vw = cv2.VideoWriter(str(RES / "ronda_original.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 5, (681, 454))
    for q in quadros:
        vw.write(cv2.cvtColor(q, cv2.COLOR_RGB2BGR))
    vw.release()

    nome, lat, lon = BAIRROS[0]
    r = visao.processar_sequencia(RES / "ronda_original.mp4", saida=RES / "ronda_anotada.mp4",
                                  latitude=lat, longitude=lon, bairro=nome)
    prev = [x["classe"] == "fissura" for x in r["resultados"]]
    acc = float(np.mean([p == v for p, v in zip(prev, verdade)]))
    (RES / "ocorrencias_demo.json").write_text(json.dumps(r["ocorrencias"], indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    print(f"ronda: {r['quadros']} quadros, acerto por quadro={acc:.0%}, {len(r['ocorrencias'])} ocorrências, "
          f"{r['latencia_media_ms']} ms/quadro, {r['fps']} FPS (com Grad-CAM e gravação)")

    # figura com 4 quadros anotados
    idx = [0, 2, 3, 9]
    fig, axs = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, i in zip(axs.flat, idx):
        res = visao.analisar_imagem(quadros[i], latitude=lat, longitude=lon, bairro=nome)
        ax.imshow(res["imagem_anotada"]); ax.axis("off")
        ax.set_title(f"quadro {i} — real: {'fissura' if verdade[i] else 'sem'}", fontsize=9)
    fig.tight_layout(); fig.savefig(RES / "quadros_exemplo.png", dpi=100); plt.close(fig)

    # benchmark
    rec = Image.fromarray(quadros[2][:227, :227])
    perf = {
        "equipamento": {"cpu": platform.processor(), "so": platform.platform(),
                        "threads_torch": torch.get_num_threads(), "gpu": "não usada (CPU)",
                        "torch": torch.__version__},
        "recorte_227x227_sem_gradcam": bench(lambda: visao.analisar_imagem(rec, explicar=False), 100),
        "recorte_227x227_com_gradcam": bench(lambda: visao.analisar_imagem(rec, explicar=True), 50),
        "quadro_681x454_sem_gradcam": bench(lambda: visao.analisar_imagem(quadros[2], explicar=False), 50),
        "quadro_681x454_com_gradcam": bench(lambda: visao.analisar_imagem(quadros[2], explicar=True), 30),
        "lote_32_recortes_224": bench(lambda: visao.prever_lote([rec] * 32), 20),
        "ronda_video": {"quadros": r["quadros"], "latencia_media_ms": r["latencia_media_ms"], "fps": r["fps"],
                        "acerto_por_quadro": acc, "ocorrencias": len(r["ocorrencias"])},
    }
    perf["lote_32_recortes_224"]["recortes_por_s"] = round(32 * perf["lote_32_recortes_224"]["fps"], 1)
    (RES / "desempenho.json").write_text(json.dumps(perf, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(perf, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
