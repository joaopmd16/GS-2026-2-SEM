"""Avalia o STT com WER (jiwer) e compara dois tamanhos de Whisper.
Pré-requisito: gravar os 20 áudios de testes/stt_roteiro.csv em testes/audios/
(>= 3 vozes, 5 com ruído de fundo). Uso: python testes/avaliar_stt.py base small"""
import csv
import re
import sys
import time
import unicodedata
from pathlib import Path

import jiwer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistente.stt import WhisperSTT  # noqa: E402

RAIZ = Path(__file__).resolve().parent


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def wer_lista(itens):
    if not itens:
        return None
    return round(jiwer.wer([norm(d["referencia"]) for d in itens],
                           [norm(d["transcricao"]) for d in itens]), 3)


def main():
    modelos = sys.argv[1:] or ["base", "small"]
    linhas = list(csv.DictReader(open(RAIZ / "stt_roteiro.csv", encoding="utf-8")))
    resumo, detalhe = [], []
    for m in modelos:
        stt = WhisperSTT(m)
        sub, tempos = [], []
        for r in linhas:
            audio = RAIZ / "audios" / r["arquivo"]
            if not audio.exists():
                continue
            t = time.perf_counter()
            hip = stt.transcrever(str(audio), apagar_depois=False)  # material de teste consentido
            tempos.append(time.perf_counter() - t)
            d = {"modelo": m, "arquivo": r["arquivo"], "locutor": r["locutor"], "ruido": r["ruido"],
                 "referencia": r["referencia"], "transcricao": hip,
                 "wer": round(jiwer.wer(norm(r["referencia"]), norm(hip) or "-"), 3)}
            sub.append(d)
        if not sub:
            sys.exit("Nenhum áudio em testes/audios/. Grave conforme testes/stt_roteiro.csv.")
        detalhe += sub
        lin = {"modelo": f"whisper-{m}", "n_audios": len(sub), "wer_geral": wer_lista(sub),
               "wer_sem_ruido": wer_lista([d for d in sub if d["ruido"] == "nao"]),
               "wer_com_ruido": wer_lista([d for d in sub if d["ruido"] == "sim"])}
        for loc in sorted({d["locutor"] for d in sub}):  # análise de viés por voz
            lin[f"wer_{loc}"] = wer_lista([d for d in sub if d["locutor"] == loc])
        lin["tempo_medio_s"] = round(sum(tempos) / len(tempos), 2)
        resumo.append(lin)
        print(lin)
    out = RAIZ.parent / "evidencias"
    for nome, dados in [("stt_detalhe.csv", detalhe), ("stt_resumo.csv", resumo)]:
        campos = list(dict.fromkeys(k for d in dados for k in d))
        with open(out / nome, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(dados)


if __name__ == "__main__":
    main()
