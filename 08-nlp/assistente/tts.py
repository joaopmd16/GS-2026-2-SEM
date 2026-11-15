"""TTS em português do Brasil. Padrão: edge-tts (voz sintética pronta
pt-BR-FranciscaNeural, nuvem). Alternativa offline: Piper (pt_BR-faber-medium).
Nenhuma voz de pessoa real é clonada."""
from __future__ import annotations

import asyncio
import subprocess
import tempfile


class EdgeTTS:
    nome = "edge-tts pt-BR-FranciscaNeural"

    def __init__(self, voz: str = "pt-BR-FranciscaNeural", velocidade: str = "-5%"):
        self.voz, self.velocidade = voz, velocidade

    def sintetizar(self, texto: str) -> str:
        import edge_tts
        saida = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name

        async def _run():
            await edge_tts.Communicate(texto, self.voz, rate=self.velocidade).save(saida)
        asyncio.run(_run())
        return saida


class PiperTTS:
    """Offline. Requer o executável `piper` e o modelo .onnx baixado."""
    nome = "piper pt_BR-faber-medium"

    def __init__(self, modelo: str = "pt_BR-faber-medium.onnx"):
        self.modelo = modelo

    def sintetizar(self, texto: str) -> str:
        saida = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        subprocess.run(["piper", "--model", self.modelo, "--output_file", saida],
                       input=texto.encode("utf-8"), check=True)
        return saida
