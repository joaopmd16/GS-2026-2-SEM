"""Adaptadores para os módulos de outras disciplinas.

Cada módulo é procurado em tempo de execução; se ainda não existir, usa-se um stub com a
MESMA assinatura. Para plugar o módulo real, basta ele expor a função indicada:

- 09-visao-computacional: `inferencia.detectar(imagem: bytes) -> {"tipo": str, "confianca": float}`
- 05-generative-ai:       `assistente.responder(mensagem: str, historico: list[dict]) -> str`
"""
from __future__ import annotations

import importlib
import io
import sys

from .repositorio import RAIZ


def _carregar(pasta: str, modulo: str, func: str):
    caminho = RAIZ / pasta
    if not (caminho / f"{modulo}.py").exists():
        return None
    sys.path.insert(0, str(caminho))
    try:
        return getattr(importlib.import_module(modulo), func)
    except Exception:  # módulo ainda em construção → stub
        return None
    finally:
        sys.path.remove(str(caminho))


def detectar_dano(imagem: bytes) -> tuple[str, float, str]:
    """Retorna (tipo, confianca, fonte)."""
    real = _carregar("09-visao-computacional", "inferencia", "detectar")
    if real:
        r = real(imagem)
        return r["tipo"], float(r["confianca"]), "modelo_visao"
    # STUB: heurística de brilho/contraste, só para demonstrar o fluxo de ponta a ponta.
    from PIL import Image, ImageStat
    img = Image.open(io.BytesIO(imagem)).convert("L").resize((128, 128))
    st = ImageStat.Stat(img)
    escuro, contraste = 1 - st.mean[0] / 255, st.stddev[0] / 128
    if escuro > 0.55:
        return "buraco", round(min(0.95, 0.5 + escuro / 2), 2), "stub"
    if contraste > 0.35:
        return "fissura", round(min(0.9, 0.4 + contraste / 2), 2), "stub"
    return "outro", 0.4, "stub"


def responder_genai(mensagem: str, historico: list[dict]) -> str | None:
    real = _carregar("05-generative-ai", "assistente", "responder")
    return real(mensagem, historico) if real else None
