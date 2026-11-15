"""Pipeline do assistente: módulo GenAI (05) → LLM direto → respostas por regras."""
from __future__ import annotations

from ..providers.llm import ErroLLM, ProvedorLLM
from ..providers.modulos import responder_genai
from ..schemas.ocorrencia import ChatEntrada, ChatResposta
from .triagem import PALAVRAS, normalizar

SISTEMA = """Você é o assistente CitizenTech de zeladoria urbana. Responda em português simples,
no máximo 4 frases, sem inventar telefones, leis ou prazos. Se o cidadão descrever um problema
na rua, sugira abrir um chamado. Responda SOMENTE JSON:
{"resposta": str, "sugestao_abrir_chamado": bool}"""

FAQ = {
    "protocolo": "Depois de confirmar um relato na aba “Reportar”, você recebe um protocolo "
                 "OC-XXXX. Acompanhe o status no painel.",
    "prazo": "O prazo depende da prioridade definida na triagem. Casos com risco a pessoas "
             "são tratados primeiro.",
    "surdo": "A plataforma funciona só por texto e alertas visuais: não é preciso ligar.",
    "foto": "Na aba “Reportar” você pode enviar uma foto (JPG ou PNG, até 5 MB). A IA sugere "
            "o tipo de dano e você confirma.",
}


def responder(e: ChatEntrada, llm: ProvedorLLM | None) -> ChatResposta:
    real = responder_genai(e.mensagem, e.historico)
    if real:
        return ChatResposta(resposta=real, fonte="modulo_genai")
    if llm:
        try:
            hist = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in e.historico[-6:])
            d = llm.json(SISTEMA, f"{hist}\nuser: {e.mensagem}")
            return ChatResposta(resposta=str(d["resposta"])[:800],
                                sugestao_abrir_chamado=bool(d.get("sugestao_abrir_chamado")),
                                fonte="llm")
        except (ErroLLM, KeyError, TypeError):
            pass  # cai nas regras abaixo
    t = normalizar(e.mensagem)
    problema = any(p in t for ps in PALAVRAS.values() for p in ps)
    for chave, resp in FAQ.items():
        if chave in t:
            return ChatResposta(resposta=resp, sugestao_abrir_chamado=problema)
    if problema:
        return ChatResposta(resposta="Parece um problema na via. Vá à aba “Reportar” para "
                                     "descrever e receber um protocolo.",
                            sugestao_abrir_chamado=True)
    return ChatResposta(resposta="Posso ajudar a reportar buracos, rachaduras e outros problemas "
                                 "da cidade, ou explicar protocolos e prazos. O que aconteceu?")
