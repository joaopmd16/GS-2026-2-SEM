"""LLM + memória da conversa + base de conhecimento (contexto recuperado no prompt).

Backends:
- OllamaLLM: modelo local via Ollama (qwen2.5:3b, llama3.2:3b, gemma2:2b...).
- ExtrativoLLM: baseline sem rede/GPU que responde com o trecho da base mais
  relevante. Serve de fallback e de comparação.
"""
from __future__ import annotations

import re

import requests

from .kb import Buscador, tokens

SYSTEM_PROMPT = """Você é a Zeladora, assistente de VOZ da zeladoria urbana da Prefeitura (Plataforma CitizenTech).
Você atende principalmente pessoas idosas, com baixa alfabetização, com deficiência visual ou motora.

Papel: orientar sobre serviços de zeladoria (buraco, calçada, iluminação, poda, entulho, bueiro, atendimento 156 e protocolos).
Tom: gentil, simples e direto. Fale como em uma ligação telefônica.
Formato: no máximo 3 frases curtas. Sem listas, sem markdown, sem emojis.
Regras:
1. Use SOMENTE as informações do CONTEXTO. Se a resposta não estiver lá, diga: "Não sei responder isso com certeza. Ligue 156 para confirmar."
2. Recuse educadamente assuntos fora da zeladoria urbana.
3. Saúde: oriente a procurar uma unidade de saúde ou ligar 192. Questões jurídicas: oriente a procurar a Defensoria Pública. Emergência com risco à vida: ligue 193 ou 199 imediatamente.
4. Nunca peça CPF, senha ou dados bancários.
"""

RECUSA = ("Desculpe, eu só posso ajudar com serviços de zeladoria da cidade, "
          "como buracos, calçadas, iluminação e poda de árvores.")
NAO_SEI = "Não sei responder isso com certeza. Ligue 156 para confirmar."

REGRAS_LIMITE = [
    (re.compile(r"(?i)\b(rem[eé]dio|dor|febre|doen[cç]a|m[eé]dico|sa[uú]de|vacina)\b"),
     "Não posso orientar sobre saúde. Procure uma unidade de saúde ou ligue 192 em caso de urgência."),
    (re.compile(r"(?i)\b(processo|advogad|processar|justi[cç]a|indeniza)"),
     "Não posso dar orientação jurídica. Procure a Defensoria Pública ou um advogado."),
    (re.compile(r"(?i)\b(inc[eê]ndio|fogo|desabamento|desabou|ferido|choque el[eé]trico|preso na enchente)\b"),
     "Isso é uma emergência. Ligue agora 193 para os Bombeiros ou 199 para a Defesa Civil."),
]

LIMIAR_ESCOPO = 2.0  # pontuação BM25 mínima para considerar a pergunta do tema


class Memoria:
    """Histórico curto da conversa (janela de N turnos)."""

    def __init__(self, max_turnos: int = 6):
        self.max_turnos = max_turnos
        self.msgs: list[dict] = []
        self.ultimo_servico = ""  # tema do turno anterior (resolve "isso", "lá"...)

    def add(self, role: str, content: str):
        self.msgs.append({"role": role, "content": content})
        self.msgs = self.msgs[-2 * self.max_turnos:]

    def ultima_pergunta(self) -> str:
        return next((m["content"] for m in reversed(self.msgs) if m["role"] == "user"), "")

    def limpar(self):
        self.msgs.clear()
        self.ultimo_servico = ""


def eh_continuacao(pergunta: str) -> bool:
    """Pergunta curta/anafórica ('e onde eu faço isso?') depende do turno anterior."""
    t = pergunta.lower().strip()
    return len(tokens(t)) <= 3 or t.startswith(("e ", "e o", "e a", "e se", "mas ")) or \
        bool(re.search(r"\b(isso|disso|nisso|ele|ela|esse|essa|lá|dele|dela)\b", t))


class BaseLLM:
    nome = "base"

    def __init__(self, buscador: Buscador):
        self.buscador = buscador

    def preparar(self, pergunta: str, memoria: Memoria):
        """Aplica os limites e recupera o contexto (considerando a memória)."""
        for regex, resposta in REGRAS_LIMITE:
            if regex.search(pergunta):
                return resposta, []
        consulta = pergunta
        if eh_continuacao(pergunta) and memoria.ultimo_servico:
            consulta = pergunta + " " + memoria.ultimo_servico
        achados = self.buscador.buscar(consulta, k=3)
        if not achados or achados[0][0] < LIMIAR_ESCOPO:
            return RECUSA, achados
        memoria.ultimo_servico = achados[0][1].servico
        return None, achados

    def responder(self, pergunta: str, memoria: Memoria) -> str:
        raise NotImplementedError


class ExtrativoLLM(BaseLLM):
    nome = "extrativo-bm25"

    def responder(self, pergunta: str, memoria: Memoria) -> str:
        pronta, achados = self.preparar(pergunta, memoria)
        resp = pronta or f"Sobre {achados[0][1].servico.lower()}: {achados[0][1].texto}"
        memoria.add("user", pergunta)
        memoria.add("assistant", resp)
        return resp


class OllamaLLM(BaseLLM):
    def __init__(self, buscador: Buscador, modelo: str = "qwen2.5:3b",
                 url: str = "http://localhost:11434", temperatura: float = 0.2):
        super().__init__(buscador)
        self.modelo, self.url, self.temperatura = modelo, url, temperatura
        self.nome = f"ollama:{modelo}"

    def responder(self, pergunta: str, memoria: Memoria) -> str:
        pronta, achados = self.preparar(pergunta, memoria)
        if pronta:
            resp = pronta
        else:
            contexto = "\n".join(f"- [{s.servico} / {s.topico}] {s.texto}" for _, s in achados)
            msgs = [{"role": "system", "content": SYSTEM_PROMPT + "\nCONTEXTO:\n" + contexto}]
            msgs += memoria.msgs + [{"role": "user", "content": pergunta}]
            r = requests.post(f"{self.url}/api/chat", timeout=120, json={
                "model": self.modelo, "messages": msgs, "stream": False,
                "options": {"temperature": self.temperatura, "num_predict": 160}})
            r.raise_for_status()
            resp = r.json()["message"]["content"].strip() or NAO_SEI
        memoria.add("user", pergunta)
        memoria.add("assistant", resp)
        return resp


def ollama_disponivel(url: str = "http://localhost:11434") -> bool:
    try:
        return requests.get(f"{url}/api/tags", timeout=2).ok
    except requests.RequestException:
        return False
