"""STT (Speech-to-Text) em português com faster-whisper (local).
Trocar o componente = implementar outra classe com o método transcrever()."""
from __future__ import annotations

import os


class WhisperSTT:
    def __init__(self, modelo: str = "small", device: str | None = None):
        self.modelo = modelo
        self.nome = f"faster-whisper-{modelo}"
        self._carregar(device or os.environ.get("STT_DEVICE") or ("cuda" if _tem_cuda() else "cpu"))

    def _carregar(self, device: str):
        from faster_whisper import WhisperModel
        self.device = device
        self.model = WhisperModel(self.modelo, device=device,
                                  compute_type="float16" if device == "cuda" else "int8")

    def _rodar(self, caminho: str) -> str:
        try:
            segs, _ = self.model.transcribe(caminho, language="pt", beam_size=5, vad_filter=True)
            return " ".join(s.text.strip() for s in segs).strip()
        except TypeError:  # PyAV >= 15 mudou a API usada pelo faster-whisper
            segs, _ = self.model.transcribe(_decodificar(caminho), language="pt",
                                            beam_size=5, vad_filter=True)
            return " ".join(s.text.strip() for s in segs).strip()

    def transcrever(self, caminho_audio: str, apagar_depois: bool = True) -> str:
        try:
            try:
                return self._rodar(caminho_audio)
            except RuntimeError as e:  # GPU sem cuBLAS/cuDNN: cai para CPU
                if self.device != "cuda":
                    raise
                print(f"[STT] GPU indisponível ({e}); usando CPU.")
                self._carregar("cpu")
                return self._rodar(caminho_audio)
        finally:
            # LGPD: retenção mínima, o áudio não é guardado após a transcrição
            if apagar_depois and caminho_audio and os.path.exists(caminho_audio):
                try:
                    os.remove(caminho_audio)
                except OSError:
                    pass


def _decodificar(caminho: str, sr: int = 16000):
    """Decodifica qualquer áudio para float32 mono 16 kHz com PyAV."""
    import av
    import numpy as np
    partes = []
    with av.open(caminho) as cont:
        res = av.AudioResampler(format="s16", layout="mono", rate=sr)
        for frame in cont.decode(audio=0):
            for f in res.resample(frame):
                partes.append(f.to_ndarray().reshape(-1))
        for f in res.resample(None):
            partes.append(f.to_ndarray().reshape(-1))
    return (np.concatenate(partes).astype(np.float32) / 32768.0) if partes else np.zeros(0, np.float32)


def _tem_cuda() -> bool:
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() == 0:
            return False
        if os.name == "nt":  # GPU sem as DLLs do CUDA 12 trava/falha: usa CPU
            import ctypes
            ctypes.CDLL("cublas64_12.dll")
        return True
    except Exception:
        return False
