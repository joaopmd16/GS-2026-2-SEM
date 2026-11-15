"""Módulo de Visão Computacional do CitizenTech — detecção de fissuras em concreto.

API pública (para o front-end 04-frontend e para o RPA 01-rpa-ia):

    from visao import analisar_imagem, processar_sequencia

    r = analisar_imagem("foto.jpg", latitude=-23.55, longitude=-46.63, bairro="Sé")
    r["classe"]            # "fissura" | "sem_fissura"
    r["confianca"]         # probabilidade de fissura (0..1) da imagem
    r["imagem_anotada"]    # numpy RGB: mapa de calor Grad-CAM + caixas nos trechos com fissura
    r["ocorrencia"]        # dict no contrato Ocorrência (ou None se não houver fissura)

Como funciona: a foto é dividida em janelas ~227 px (o mesmo tamanho dos recortes do
treino); cada janela é classificada pela MobileNetV3-Small ajustada. A confiança da
imagem é a maior probabilidade entre as janelas; janelas acima do limiar recebem
caixa. O Grad-CAM mostra quais pixels (as próprias linhas da fissura) levaram à decisão.

Aviso: é apoio à TRIAGEM de locais para inspeção. A presença de fissura na imagem não
indica gravidade nem segurança estrutural — isso exige vistoria técnica.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from itertools import count
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw
from torchvision import models

RAIZ = Path(__file__).parent
PESOS = RAIZ / "modelo" / "mobilenetv3_fissuras.pt"
CONFIG = RAIZ / "modelo" / "config.json"
TAM = 224                       # entrada da rede
JANELA = 227                    # tamanho dos recortes do dataset
MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DESVIO = np.array([0.229, 0.224, 0.225], dtype=np.float32)
torch.set_num_threads(max(1, torch.get_num_threads()))


def criar_modelo(pretreinado: bool = True) -> nn.Module:
    """MobileNetV3-Small (ImageNet) com a cabeça trocada para 1 saída (logit de fissura)."""
    pesos = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretreinado else None
    m = models.mobilenet_v3_small(weights=pesos)
    m.classifier[3] = nn.Linear(m.classifier[3].in_features, 1)
    return m


def preprocessar(img: Image.Image) -> torch.Tensor:
    """Redimensiona para 224x224, escala 0..1 e normaliza com média/desvio do ImageNet."""
    a = np.asarray(img.convert("RGB").resize((TAM, TAM), Image.BILINEAR), dtype=np.float32) / 255.0
    a = (a - MEDIA) / DESVIO
    return torch.from_numpy(a.transpose(2, 0, 1))


_modelo = None
_limiar = 0.5


def carregar():
    global _modelo, _limiar
    if _modelo is None:
        m = criar_modelo(pretreinado=False)
        m.load_state_dict(torch.load(PESOS, map_location="cpu"))
        m.eval()
        _modelo = m
        if CONFIG.exists():
            _limiar = json.loads(CONFIG.read_text(encoding="utf-8")).get("limiar", 0.5)
    return _modelo, _limiar


@torch.no_grad()
def prever_lote(imgs: list[Image.Image]) -> np.ndarray:
    """Probabilidade de fissura para cada imagem/recorte."""
    m, _ = carregar()
    x = torch.stack([preprocessar(i) for i in imgs])
    return torch.sigmoid(m(x)).squeeze(1).numpy()


def _janelas(img: Image.Image, max_lado: int = 908):
    """Reduz fotos grandes (até 4x4 janelas) e devolve as caixas das janelas."""
    w, h = img.size
    esc = min(1.0, max_lado / max(w, h))
    if esc < 1:
        img = img.resize((int(w * esc), int(h * esc)), Image.BILINEAR)
        w, h = img.size
    if w <= JANELA * 1.5 and h <= JANELA * 1.5:
        return img, [(0, 0, w, h)]
    nx, ny = max(1, round(w / JANELA)), max(1, round(h / JANELA))
    sx, sy = w / nx, h / ny
    return img, [(int(i * sx), int(j * sy), int((i + 1) * sx), int((j + 1) * sy))
                 for j in range(ny) for i in range(nx)]


def gradcam(img: Image.Image) -> np.ndarray:
    """Grad-CAM na última camada convolucional: mapa (224x224, 0..1) das características
    visuais que mais pesaram para a classe 'fissura'."""
    m, _ = carregar()
    camada = m.features[-1]
    ativ, grad = {}, {}
    def _fw(_m, _i, o):
        o = o.clone()  # a ativação Hardswish é in-place; clonar permite capturar o gradiente
        ativ["a"] = o
        o.register_hook(lambda g: grad.setdefault("g", g))
        return o

    h1 = camada.register_forward_hook(_fw)
    try:
        x = preprocessar(img).unsqueeze(0).requires_grad_(True)
        m.zero_grad()
        m(x)[0, 0].backward()
    finally:
        h1.remove()
    pesos = grad["g"].mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((pesos * ativ["a"]).sum(1))[0].detach().numpy()
    cam = np.asarray(Image.fromarray(cam).resize((TAM, TAM), Image.BILINEAR))
    return cam / (cam.max() + 1e-8)


def _colorir(cam: np.ndarray) -> np.ndarray:
    """Colormap simples (azul→vermelho) sem depender do OpenCV."""
    r = np.clip(1.5 - np.abs(4 * cam - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * cam - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * cam - 1), 0, 1)
    return (np.stack([r, g, b], -1) * 255).astype(np.uint8)


_seq = count(1)


def _prioridade(conf: float, frac: float) -> str:
    # heurística de TRIAGEM (não é laudo): confiança alta e fissura em boa parte da imagem
    if conf >= 0.95 and frac >= 0.5:
        return "alta"
    if conf >= 0.8:
        return "media"
    return "baixa"


def gerar_ocorrencia(confianca: float, frac: float, latitude=None, longitude=None,
                     bairro: str = "", id_: str | None = None) -> dict:
    return {
        "id": id_ or f"OC-VC-{datetime.now():%Y%m%d%H%M%S}-{next(_seq):03d}",
        "tipo": "fissura",
        "origem": "visao",
        "descricao": (f"Possível fissura em superfície de concreto detectada por visão computacional "
                      f"({frac:.0%} da área analisada). Triagem automática — requer vistoria técnica."),
        "confianca": round(float(confianca), 4),
        "latitude": latitude,
        "longitude": longitude,
        "bairro": bairro,
        "prioridade": _prioridade(confianca, frac),
        "status": "aberta",
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def analisar_imagem(imagem, latitude: float | None = None, longitude: float | None = None,
                    bairro: str = "", explicar: bool = True, limiar: float | None = None) -> dict:
    """Função principal para o front-end.

    imagem: caminho, PIL.Image ou numpy RGB (ex.: valor de gr.Image / st.file_uploader aberto).
    Retorna dict com classe, confianca, limiar, janelas, latencia_ms, imagem_anotada (np RGB)
    e ocorrencia (contrato Ocorrência) quando há fissura.
    """
    t0 = time.perf_counter()
    if isinstance(imagem, (str, Path)):
        img = Image.open(imagem)
    elif isinstance(imagem, np.ndarray):
        img = Image.fromarray(imagem)
    else:
        img = imagem
    img = img.convert("RGB")
    _, lim_padrao = carregar()
    lim = lim_padrao if limiar is None else limiar

    img, caixas = _janelas(img)
    probs = prever_lote([img.crop(c) for c in caixas])
    conf = float(probs.max())
    positivas = [(c, p) for c, p in zip(caixas, probs) if p >= lim]
    frac = len(positivas) / len(caixas)
    classe = "fissura" if conf >= lim else "sem_fissura"

    # visual: Grad-CAM em cada janela positiva + caixa com a confiança
    vis = np.asarray(img).copy()
    if explicar:
        for (x0, y0, x1, y1), _ in positivas:
            cam = gradcam(img.crop((x0, y0, x1, y1)))
            cam = np.asarray(Image.fromarray((cam * 255).astype(np.uint8)).resize((x1 - x0, y1 - y0))) / 255.0
            cor = _colorir(cam)
            alfa = (0.55 * cam)[..., None]
            vis[y0:y1, x0:x1] = (vis[y0:y1, x0:x1] * (1 - alfa) + cor * alfa).astype(np.uint8)
    pil = Image.fromarray(vis)
    d = ImageDraw.Draw(pil)
    for (x0, y0, x1, y1), p in positivas:
        d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 0, 0), width=3)
        d.text((x0 + 4, y0 + 4), f"fissura {p:.0%}", fill=(255, 255, 0))
    cor_b = (220, 0, 0) if classe == "fissura" else (0, 150, 0)
    d.rectangle((0, 0, pil.width, 18), fill=cor_b)
    d.text((4, 3), f"{classe.upper()}  confianca={conf:.1%}  limiar={lim:.2f}", fill=(255, 255, 255))

    return {
        "classe": classe,
        "confianca": round(conf, 4),
        "limiar": lim,
        "janelas": [{"caixa": list(c), "prob_fissura": round(float(p), 4)} for c, p in zip(caixas, probs)],
        "fracao_area_fissura": round(frac, 3),
        "latencia_ms": round((time.perf_counter() - t0) * 1000, 1),
        "imagem_anotada": np.asarray(pil),
        "ocorrencia": gerar_ocorrencia(conf, frac, latitude, longitude, bairro) if classe == "fissura" else None,
        "aviso": "Triagem automática: não determina gravidade nem segurança estrutural.",
    }


def processar_sequencia(fonte, saida: str | Path | None = None, passo: int = 1, **geo) -> dict:
    """Simula monitoramento urbano: processa um vídeo (.mp4/.avi) ou uma lista/pasta de imagens.

    Gera (opcional) um vídeo anotado em `saida` e devolve as métricas de desempenho
    (latência média, FPS) e a lista de ocorrências geradas (uma por trecho contínuo com fissura).
    """
    import cv2  # só necessário para vídeo
    if isinstance(fonte, (list, tuple)):
        quadros = (np.asarray(Image.open(p).convert("RGB")) for p in fonte)
    elif Path(fonte).is_dir():
        quadros = (np.asarray(Image.open(p).convert("RGB")) for p in sorted(Path(fonte).glob("*.jpg")))
    else:
        cap = cv2.VideoCapture(str(fonte))

        def _ler():
            i = 0
            while True:
                ok, f = cap.read()
                if not ok:
                    break
                if i % passo == 0:
                    yield cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                i += 1
            cap.release()
        quadros = _ler()

    escritor, resultados, ocorrencias, lat = None, [], [], []
    em_trecho = False
    t_total = time.perf_counter()
    for i, q in enumerate(quadros):
        r = analisar_imagem(q, explicar=True, **geo)
        lat.append(r["latencia_ms"])
        resultados.append({"quadro": i, "classe": r["classe"], "confianca": r["confianca"]})
        if r["ocorrencia"] and not em_trecho:          # abre 1 ocorrência por trecho com fissura
            ocorrencias.append(r["ocorrencia"])
        em_trecho = r["classe"] == "fissura"
        if saida:
            a = cv2.cvtColor(r["imagem_anotada"], cv2.COLOR_RGB2BGR)
            if escritor is None:
                escritor = cv2.VideoWriter(str(saida), cv2.VideoWriter_fourcc(*"mp4v"), 5, (a.shape[1], a.shape[0]))
                tam_video = (a.shape[1], a.shape[0])
            escritor.write(cv2.resize(a, tam_video))
    if escritor:
        escritor.release()
    dur = time.perf_counter() - t_total
    return {
        "quadros": len(resultados),
        "latencia_media_ms": round(float(np.mean(lat)), 1) if lat else None,
        "fps": round(len(resultados) / dur, 2) if dur else None,
        "resultados": resultados,
        "ocorrencias": ocorrencias,
    }


if __name__ == "__main__":
    import sys
    r = analisar_imagem(sys.argv[1])
    Image.fromarray(r.pop("imagem_anotada")).save("saida_anotada.jpg")
    print(json.dumps(r, ensure_ascii=False, indent=2))
