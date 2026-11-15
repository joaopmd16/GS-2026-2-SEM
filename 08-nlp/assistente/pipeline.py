"""Orquestra microfone → STT → LLM → adaptação para fala → TTS, medindo a latência
de cada etapa. Cada componente é injetado e pode ser trocado isoladamente."""
from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from .fala import adaptar_para_fala
from .llm import Memoria

LOG_LATENCIA = Path(__file__).resolve().parent.parent / "evidencias" / "latencia_log.csv"


@dataclass
class Turno:
    transcricao: str
    resposta_texto: str
    resposta_falada: str
    audio_resposta: str | None
    latencia: dict = field(default_factory=dict)


class AssistenteVoz:
    def __init__(self, stt, llm, tts, memoria: Memoria | None = None, registrar=True):
        self.stt, self.llm, self.tts = stt, llm, tts
        self.memoria = memoria or Memoria()
        self.registrar = registrar

    def turno(self, audio: str | None = None, texto: str | None = None) -> Turno:
        lat = {}
        t0 = time.perf_counter()
        if audio and self.stt:
            transcricao = self.stt.transcrever(audio)  # apaga o áudio depois
        else:
            transcricao = texto or ""
        lat["stt_s"] = time.perf_counter() - t0

        t1 = time.perf_counter()
        resposta = self.llm.responder(transcricao, self.memoria)
        lat["llm_s"] = time.perf_counter() - t1

        t2 = time.perf_counter()
        falada = adaptar_para_fala(resposta)
        lat["adaptacao_s"] = time.perf_counter() - t2

        t3 = time.perf_counter()
        audio_resp = self.tts.sintetizar(falada) if self.tts else None
        lat["tts_s"] = time.perf_counter() - t3
        lat["total_ate_fala_s"] = time.perf_counter() - t0
        lat = {k: round(v, 3) for k, v in lat.items()}

        if self.registrar:
            self._log(transcricao, lat)
        return Turno(transcricao, resposta, falada, audio_resp, lat)

    def _log(self, transcricao: str, lat: dict):
        LOG_LATENCIA.parent.mkdir(exist_ok=True)
        novo = not LOG_LATENCIA.exists()
        with open(LOG_LATENCIA, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if novo:
                w.writerow(["quando", "stt", "llm", "tts", "chars_pergunta", *lat.keys()])
            # LGPD: o log guarda só o tamanho da pergunta, não o conteúdo
            w.writerow([datetime.now().isoformat(timespec="seconds"),
                        getattr(self.stt, "nome", "texto"), self.llm.nome,
                        getattr(self.tts, "nome", "-"), len(transcricao), *lat.values()])
