"""10 conversas completas (3 turnos cada) de ponta a ponta, com latência por etapa.
Modo texto (padrão): a pergunta entra como texto (STT = 0 s).
Modo áudio (--audio): usa testes/audios/e2e_<conversa>_<turno>.wav com Whisper.
Uso: python testes/conversas_e2e.py [--llm extrativo|qwen2.5:3b] [--sem-tts] [--audio]"""
import argparse
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistente.kb import Buscador, construir  # noqa: E402
from assistente.llm import ExtrativoLLM, Memoria, OllamaLLM  # noqa: E402
from assistente.pipeline import AssistenteVoz  # noqa: E402

CONVERSAS = [
    ["Tem um buraco grande na minha rua.", "E quanto tempo demora isso?", "Quanto custa?"],
    ["A lâmpada do poste está apagada.", "E qual é o prazo?", "Me receita um remédio para dor de cabeça."],
    ["A calçada da frente de casa está quebrada.", "De quem é a responsabilidade?", "E como eu peço o conserto?"],
    ["Como eu peço a poda de uma árvore?", "E quanto tempo demora isso?", "Posso podar sozinho?"],
    ["Jogaram entulho na esquina.", "E se eu quiser denunciar?", "Onde eu levo o entulho da minha reforma?"],
    ["O bueiro está entupido.", "E qual o prazo para a limpeza?", "E se tiver enchente com risco à vida?"],
    ["Sou surdo, como falo com a Prefeitura?", "Qual é o horário de atendimento?", "Como eu acompanho meu protocolo?"],
    ["Preciso de uma rampa de acessibilidade na esquina.", "E o prazo da vistoria?", "Qual time vai ganhar o campeonato?"],
    ["Tem um poste caído com fio solto.", "E a lâmpada queimada, quanto tempo leva?", "É de graça?"],
    ["Como eu apago meus dados da Prefeitura?", "Vocês seguem a LGPD?", "Obrigado, era só isso."],
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", default="extrativo")
    ap.add_argument("--sem-tts", action="store_true")
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--whisper", default="small")
    a = ap.parse_args()
    raiz = Path(__file__).resolve().parent.parent
    busc = Buscador(construir(raiz / "base_conhecimento" / "documentos")[0])
    llm = ExtrativoLLM(busc) if a.llm == "extrativo" else OllamaLLM(busc, a.llm)
    tts = stt = None
    if not a.sem_tts:
        from assistente.tts import EdgeTTS
        tts = EdgeTTS()
    if a.audio:
        from assistente.stt import WhisperSTT
        stt = WhisperSTT(a.whisper)

    linhas = []
    for c, turnos in enumerate(CONVERSAS, 1):
        ass = AssistenteVoz(stt, llm, tts, Memoria())
        for t, pergunta in enumerate(turnos, 1):
            audio = raiz / "testes" / "audios" / f"e2e_{c:02d}_{t}.wav"
            r = ass.turno(audio=str(audio) if stt and audio.exists() else None, texto=pergunta)
            linhas.append({"conversa": c, "turno": t, "pergunta": r.transcricao,
                           "resposta": r.resposta_texto, "texto_falado": r.resposta_falada,
                           **r.latencia})
            print(c, t, r.latencia)
    out = raiz / "evidencias" / f"e2e_{llm.nome.replace(':', '_')}{'_sem_tts' if a.sem_tts else ''}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys())
        w.writeheader()
        w.writerows(linhas)
    print("\nLatência média (s):")
    for k in ["stt_s", "llm_s", "adaptacao_s", "tts_s", "total_ate_fala_s"]:
        print(f"  {k}: {statistics.mean(l[k] for l in linhas):.3f}")


if __name__ == "__main__":
    main()
