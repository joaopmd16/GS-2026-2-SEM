"""Etapas 2 e 3 — Transfer learning (MobileNetV3-Small/ImageNet) e avaliação.

    python treinar.py --origem <pasta do dataset> [--epocas 3]

Saídas:
  modelo/mobilenetv3_fissuras.pt, modelo/config.json (limiar escolhido na validação)
  resultados/metricas.json, matriz_confusao.png, curva_limiar.png,
  acertos_erros.png (exemplos + Grad-CAM), erros_teste.csv
"""
import argparse
import csv
import json
import random
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageEnhance
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from torch.utils.data import DataLoader, Dataset

import visao

RAIZ = Path(__file__).parent
RES = RAIZ / "resultados"
torch.manual_seed(42); random.seed(42); np.random.seed(42)


class Recortes(Dataset):
    def __init__(self, linhas, origem, aumentar=False):
        self.l, self.o, self.aum = linhas, Path(origem), aumentar

    def __len__(self):
        return len(self.l)

    def __getitem__(self, i):
        cam, rot = self.l[i]
        img = Image.open(self.o / cam).convert("RGB")
        if self.aum:  # fissuras não têm orientação nem iluminação fixas
            if random.random() < .5: img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if random.random() < .5: img = img.transpose(Image.FLIP_TOP_BOTTOM)
            img = img.rotate(random.choice([0, 90, 180, 270]))
            img = ImageEnhance.Brightness(img).enhance(random.uniform(.6, 1.4))
            img = ImageEnhance.Contrast(img).enhance(random.uniform(.7, 1.3))
        return visao.preprocessar(img), torch.tensor(float(rot))


@torch.no_grad()
def inferir(m, dl):
    m.eval(); ps, ys = [], []
    for x, y in dl:
        ps.append(torch.sigmoid(m(x)).squeeze(1)); ys.append(y)
    return torch.cat(ps).numpy(), torch.cat(ys).numpy().astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", required=True)
    ap.add_argument("--epocas", type=int, default=3)
    a = ap.parse_args()
    RES.mkdir(exist_ok=True); (RAIZ / "modelo").mkdir(exist_ok=True)

    conj = {"treino": [], "validacao": [], "teste": []}
    with open(RAIZ / "dados" / "split.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            conj[r["conjunto"]].append((r["caminho"], int(r["rotulo"])))
    dl = {k: DataLoader(Recortes(v, a.origem, k == "treino"), batch_size=64, shuffle=k == "treino")
          for k, v in conj.items()}

    m = visao.criar_modelo(pretreinado=True)
    # congela as camadas iniciais (bordas/texturas genéricas do ImageNet) e ajusta as finais
    for p in m.features[:9].parameters():
        p.requires_grad = False
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=1e-3, weight_decay=1e-4)
    perda = nn.BCEWithLogitsLoss()
    hist = []
    t0 = time.time()
    for ep in range(a.epocas):
        m.train(); tot = 0
        for x, y in dl["treino"]:
            opt.zero_grad(); l = perda(m(x).squeeze(1), y); l.backward(); opt.step()
            tot += l.item() * len(y)
        pv, yv = inferir(m, dl["validacao"])
        hist.append({"epoca": ep + 1, "perda_treino": tot / len(conj["treino"]),
                     "f1_validacao": f1_score(yv, pv >= .5)})
        print(hist[-1], f"{time.time() - t0:.0f}s")
    tempo_treino = time.time() - t0
    torch.save(m.state_dict(), visao.PESOS)

    # limiar: maximiza F1 na VALIDAÇÃO com recall >= 0.97 (perder fissura custa mais que
    # uma inspeção extra). Nunca escolhido no teste.
    pv, yv = inferir(m, dl["validacao"])
    grade = np.round(np.arange(.05, .96, .05), 2)
    curva = [(t, precision_score(yv, pv >= t, zero_division=0), recall_score(yv, pv >= t), f1_score(yv, pv >= t))
             for t in grade]
    candidatos = [c for c in curva if c[2] >= .97] or curva
    limiar = float(max(candidatos, key=lambda c: c[3])[0])
    visao.CONFIG.write_text(json.dumps({"limiar": limiar, "arquitetura": "mobilenet_v3_small",
                                        "entrada": [224, 224]}, indent=2), encoding="utf-8")

    pt, yt = inferir(m, dl["teste"])
    yh = (pt >= limiar).astype(int)
    met = {
        "dataset": "Concrete Crack Images for Classification (Özgenel 2019) — amostra",
        "n": {k: len(v) for k, v in conj.items()},
        "limiar": limiar,
        "teste": {"acuracia": float((yh == yt).mean()), "precisao": precision_score(yt, yh),
                  "recall": recall_score(yt, yh), "f1": f1_score(yt, yh), "roc_auc": roc_auc_score(yt, pt),
                  "matriz_confusao": confusion_matrix(yt, yh).tolist()},
        "teste_limiar_0.5": {"precisao": precision_score(yt, pt >= .5), "recall": recall_score(yt, pt >= .5),
                             "f1": f1_score(yt, pt >= .5)},
        "historico": hist, "tempo_treino_s": round(tempo_treino, 1),
    }
    (RES / "metricas.json").write_text(json.dumps(met, indent=2, ensure_ascii=False), encoding="utf-8")
    print(classification_report(yt, yh, target_names=["sem_fissura", "fissura"], digits=4))
    print(json.dumps(met["teste"], indent=2))

    # --- figuras
    cm = np.array(met["teste"]["matriz_confusao"])
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], ["sem_fissura", "fissura"]); ax.set_yticks([0, 1], ["sem_fissura", "fissura"])
    ax.set_xlabel("Previsto"); ax.set_ylabel("Real"); ax.set_title(f"Teste (limiar {limiar})")
    fig.tight_layout(); fig.savefig(RES / "matriz_confusao.png", dpi=120); plt.close(fig)

    c = np.array(curva)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for k, n in ((1, "precisão"), (2, "recall"), (3, "F1")):
        ax.plot(c[:, 0], c[:, k], label=n)
    ax.axvline(limiar, ls="--", c="gray"); ax.set_xlabel("limiar"); ax.set_ylim(.8, 1.005)
    ax.legend(); ax.set_title("Escolha do limiar (validação)")
    fig.tight_layout(); fig.savefig(RES / "curva_limiar.png", dpi=120); plt.close(fig)

    # erros do teste + exemplos de acerto, com Grad-CAM
    erros = [(conj["teste"][i][0], int(yt[i]), float(pt[i])) for i in np.where(yh != yt)[0]]
    with open(RES / "erros_teste.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["caminho", "real", "prob_fissura"]); w.writerows(erros)
    visao._modelo = None  # recarrega pesos salvos
    acertos = [(conj["teste"][i][0], int(yt[i]), float(pt[i])) for i in np.where(yh == yt)[0]]
    random.shuffle(acertos)
    amostra = [x for x in acertos if x[1] == 1][:3] + [x for x in acertos if x[1] == 0][:2] + erros[:5]
    fig, axs = plt.subplots(2, len(amostra), figsize=(2.2 * len(amostra), 4.8))
    for k, (cam, real, p) in enumerate(amostra):
        img = Image.open(Path(a.origem) / cam).convert("RGB")
        mapa = visao.gradcam(img)
        axs[0, k].imshow(img); axs[1, k].imshow(img.resize((224, 224))); axs[1, k].imshow(mapa, cmap="jet", alpha=.45)
        tipo = "ERRO" if (p >= limiar) != bool(real) else "acerto"
        axs[0, k].set_title(f"{tipo}\nreal={'F' if real else 'S'} p={p:.2f}", fontsize=8,
                            color="red" if tipo == "ERRO" else "black")
        axs[0, k].axis("off"); axs[1, k].axis("off")
    fig.suptitle("Acertos e erros no teste (linha de baixo: Grad-CAM)  F=fissura S=sem")
    fig.tight_layout(); fig.savefig(RES / "acertos_erros.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
