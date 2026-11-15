"""Interface Gradio do assistente de voz "Zeladora".

Rodar:  python app.py            (usa Ollama se estiver no ar; senão, o baseline extrativo)
        python app.py --llm extrativo --whisper base --share
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import gradio as gr

from assistente.kb import Buscador, construir
from assistente.llm import ExtrativoLLM, Memoria, OllamaLLM, ollama_disponivel
from assistente.pipeline import AssistenteVoz
from assistente.stt import WhisperSTT
from assistente.tts import EdgeTTS

RAIZ = Path(__file__).parent
AVISO = """### Aviso de privacidade (LGPD)
Esta conversa é **gravada e processada** para responder ao seu pedido.
- O áudio é transcrito **neste computador** (Whisper) e **apagado logo depois**.
- Só o **texto da resposta** vai para o serviço de voz (edge-tts, Microsoft), que o transforma em fala.
- Não diga CPF, senhas ou dados bancários. O registro de desempenho guarda só tempos, não o que você falou.
- Para casos de saúde, jurídicos ou emergência, o assistente vai indicar o órgão certo."""


def montar(args):
    secoes, _ = construir(RAIZ / "base_conhecimento" / "documentos", RAIZ / "corpus")
    busc = Buscador(secoes)
    if args.llm == "extrativo" or not ollama_disponivel():
        llm = ExtrativoLLM(busc)
    else:
        llm = OllamaLLM(busc, modelo=args.llm)
    return WhisperSTT(args.whisper), llm, EdgeTTS()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", default="qwen2.5:3b", help="modelo Ollama ou 'extrativo'")
    ap.add_argument("--whisper", default="small")
    ap.add_argument("--share", action="store_true")
    args = ap.parse_args()
    stt, llm, tts = montar(args)

    with gr.Blocks(title="Zeladora — assistente de voz CitizenTech") as demo:
        gr.Markdown("# 🎙️ Zeladora — fale com a zeladoria da sua cidade")
        gr.Markdown(AVISO)
        consentiu = gr.Checkbox(label="Li o aviso e concordo que minha voz seja gravada e processada.")
        estado = gr.State(None)

        with gr.Row():
            audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                label="Aperte para falar ou envie um arquivo de áudio")
            texto_in = gr.Textbox(label="Ou digite (opcional)", lines=2)
        enviar = gr.Button("Enviar", variant="primary", size="lg")
        audio_out = gr.Audio(label="Resposta falada", autoplay=True)
        chat = gr.Chatbot(label="Transcrição e resposta em texto", type="messages", height=320)
        lat_out = gr.JSON(label="Latência por etapa (segundos)")
        limpar = gr.Button("Nova conversa (apaga a memória)")

        def responder(audio, texto, ok, assistente, historico):
            if not ok:
                raise gr.Error("Para continuar, marque que leu e concorda com o aviso de privacidade.")
            assistente = assistente or AssistenteVoz(stt, llm, tts, Memoria())
            caminho = None
            if audio:  # cópia temporária: o STT apaga o arquivo depois de transcrever
                caminho = tempfile.NamedTemporaryFile(suffix=Path(audio).suffix, delete=False).name
                shutil.copy(audio, caminho)
                Path(audio).unlink(missing_ok=True)
            t = assistente.turno(audio=caminho, texto=texto)
            historico = (historico or []) + [
                {"role": "user", "content": t.transcricao},
                {"role": "assistant", "content": t.resposta_texto}]
            return t.audio_resposta, historico, t.latencia, assistente, None, ""

        enviar.click(responder, [audio_in, texto_in, consentiu, estado, chat],
                     [audio_out, chat, lat_out, estado, audio_in, texto_in])
        limpar.click(lambda: (None, [], None), None, [estado, chat, lat_out])

    demo.launch(share=args.share)


if __name__ == "__main__":
    main()
