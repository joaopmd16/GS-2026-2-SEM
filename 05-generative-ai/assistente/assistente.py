"""Orquestração do RAG: guardrails de entrada -> recuperação -> sanitização do contexto
-> geração -> verificação de fundamentação -> resposta com fontes.

Função pública para o front-end: `responder(pergunta, historico=None) -> dict`.
"""
import re

from . import guardrails as g
from .generator import GeradorExtrativo, GeradorLLM, eh_sem_evidencia
from .ingest import construir_corpus
from .retriever import Retriever
from .texto import expandir_consulta, tokens

RX_OC = re.compile(r"\bOC-?\s?(\d{1,4})\b", re.I)
MSG_ABSTENCAO = ("Não encontrei essa informação na base de conhecimento da CitizenTech, então prefiro não "
                 "responder para não passar informação errada. Você pode consultar o SP156 "
                 "(telefone 156, portal ou aplicativo).")
MSG_FORA = ("Sou o assistente de zeladoria urbana da CitizenTech e só consigo ajudar com buracos, fissuras, calçadas, "
            "iluminação, entulho, acompanhamento de ocorrências, ouvidoria/LGPD e alertas sonoros.")
MSG_INJ = ("Não posso mudar minhas regras nem revelar instruções internas. Posso ajudar com dúvidas sobre "
           "zeladoria urbana ou com o status de uma ocorrência (ex.: OC-0001).")
MSG_PII = ("Por proteção de dados (LGPD), não informo dados pessoais de quem registrou ocorrências. "
           "Posso informar o tipo, bairro, status e prioridade.")
MSG_EMERG = ("ATENÇÃO: se há risco imediato à vida, ligue agora para a Defesa Civil (199) ou o Corpo de "
             "Bombeiros (193).")


class Assistente:
    def __init__(self, estrategia="estrutural", modo_retriever="hibrido", top_k=4, usar_llm=None,
                 limiar_bm25=2.0, limiar_vetorial=0.12, limiar_suporte=0.6, chunks=None):
        self.chunks = chunks or construir_corpus(estrategia)
        self.retriever = Retriever(self.chunks, modo_retriever)
        self.top_k, self.limiar_bm25, self.limiar_vetorial, self.limiar_suporte = top_k, limiar_bm25, limiar_vetorial, limiar_suporte
        llm = GeradorLLM()
        self.gerador = llm if (usar_llm if usar_llm is not None else llm.disponivel) else GeradorExtrativo()
        self.fallback = GeradorExtrativo()
        self.ocs = {c.meta["id"]: c for c in self.chunks if c.meta.get("arquivo") == "ocorrencias"}

    # ------------------------------------------------------------------ util
    def _saida(self, resposta, motivo, fontes=(), abstencao=False, laudo=None, extra=None):
        out = {"resposta": resposta, "fontes": list(fontes), "abstencao": abstencao, "motivo": motivo,
               "gerador": self.gerador.nome, "verificacao": laudo or []}
        if extra:
            out.update(extra)
        return out

    @staticmethod
    def _fonte(n, c, sc=None):
        m = c.meta
        return {"n": n, "id": c.id, "titulo": m.get("titulo"), "secao": m.get("secao"), "url": m.get("url"),
                "consultado_em": m.get("consultado_em"), "trecho": c.texto[:300], "scores": sc}

    def _expandir(self, pergunta, historico):
        """Consistência entre turnos: perguntas curtas/anafóricas herdam a última pergunta do usuário."""
        if not historico:
            return pergunta
        anteriores = [h["texto"] for h in historico if h.get("papel") == "usuario"]
        if anteriores and (len(tokens(pergunta)) <= 3 or re.search(r"\b(e |ela|ele|isso|essa|esse|dela|dele)\b", pergunta.lower())):
            return anteriores[-1] + " " + pergunta
        return pergunta

    # ------------------------------------------------------------------ main
    def responder(self, pergunta: str, historico: list[dict] | None = None) -> dict:
        pergunta = (pergunta or "").strip()[:1000]
        if not pergunta:
            return self._saida("Escreva sua dúvida sobre zeladoria urbana.", "vazia", abstencao=True)
        pergunta, pii = g.mascarar_pii(pergunta)
        extra = {"pii_removida_da_pergunta": pii} if pii else {}

        if g.detectar_injecao(pergunta):
            return self._saida(MSG_INJ, "prompt_injection_bloqueada", abstencao=True, extra=extra)
        if g.pede_dado_pessoal(pergunta):
            return self._saida(MSG_PII, "pedido_dado_pessoal_negado", abstencao=True, extra=extra)
        aviso = MSG_EMERG + " " if g.emergencia(pergunta) else ""

        # consulta direta por código de ocorrência (filtro por metadado)
        consulta = self._expandir(pergunta, historico)
        m = RX_OC.search(pergunta) or (RX_OC.search(consulta) if consulta != pergunta else None)
        if m:
            oid = f"OC-{int(m.group(1)):04d}"
            c = self.ocs.get(oid)
            if not c:
                return self._saida(f"Não encontrei a ocorrência {oid} na base. Confira o código do protocolo.",
                                   "ocorrencia_inexistente", abstencao=True, extra=extra)
            texto, alterado = g.sanitizar_contexto(c.texto)
            stat = {"aberta": "aguarda triagem", "encaminhada": "foi enviada ao órgão responsável",
                    "em_inspecao": "tem equipe designada para vistoria", "resolvida": "foi concluída pelo órgão"}
            st = c.meta.get("status", "")
            resp = (f"{aviso}A ocorrência {oid} ({c.meta.get('tipo')}, bairro {c.meta.get('bairro')}) está com status "
                    f"'{st}', ou seja, {stat.get(st, 'status não reconhecido')}. Prioridade: {c.meta.get('prioridade')} [1].")
            return self._saida(resp, "consulta_ocorrencia", [self._fonte(1, c)],
                               extra={**extra, "contexto_sanitizado": alterado})

        consulta = expandir_consulta(consulta)
        hits = self.retriever.buscar(consulta, k=self.top_k)
        hits = [(c, sc) for c, sc in hits if c.meta.get("arquivo") != "ocorrencias"] or hits
        top = hits[0][1] if hits else {"bm25": 0, "vetorial": 0}
        if top["bm25"] < self.limiar_bm25 and top["vetorial"] < self.limiar_vetorial:
            msg = aviso + (MSG_FORA if top["bm25"] == 0 else MSG_ABSTENCAO)
            return self._saida(msg.strip(), "baixa_relevancia_recuperacao", abstencao=True,
                               extra={**extra, "scores_top": top})

        # desambiguação: pergunta muito curta que casa com documentos de assuntos diferentes
        if not historico and len(tokens(pergunta)) <= 2 and len(hits) > 1:
            arquivos = {c.meta.get("arquivo") for c, _ in hits[:3]}
            if len(arquivos) >= 3:
                opcoes = "; ".join(sorted({c.meta.get("titulo") for c, _ in hits[:3]}))
                return self._saida(f"Sua pergunta pode se referir a assuntos diferentes ({opcoes}). "
                                   "Pode dar mais detalhes, por exemplo o tipo de problema?", "pergunta_ambigua",
                                   abstencao=True, extra=extra)

        trechos, fontes, contextos, sanit = [], [], {}, False
        for n, (c, sc) in enumerate(hits, 1):
            t, alt = g.sanitizar_contexto(c.texto)
            sanit |= alt
            trechos.append((n, t, c.meta))
            contextos[n] = t
            fontes.append(self._fonte(n, c, sc))

        foco = consulta
        try:
            # recupera com a consulta expandida pelo histórico, mas gera focado na pergunta atual
            foco = expandir_consulta(pergunta) if tokens(pergunta) else consulta
            bruta = self.gerador.gerar(foco, trechos)
            gerador_usado = self.gerador.nome
        except Exception as e:  # rede/API indisponível -> fallback extrativo
            bruta, gerador_usado = self.fallback.gerar(foco, trechos), f"extrativo (fallback: {type(e).__name__})"
        extra.update({"contexto_sanitizado": sanit, "resposta_bruta": bruta, "gerador": gerador_usado})

        if eh_sem_evidencia(bruta):
            return self._saida((aviso + MSG_ABSTENCAO).strip(), "gerador_sem_evidencia", fontes, True, extra=extra)
        bruta, _ = g.mascarar_pii(bruta)
        verificada, laudo = g.verificar_fundamentacao(bruta, contextos, self.limiar_suporte)
        if not verificada:
            return self._saida((aviso + MSG_ABSTENCAO).strip(), "resposta_nao_sustentada_bloqueada", fontes, True,
                               laudo, extra)
        usados = {int(x) for x in re.findall(r"\[(\d+)\]", verificada)}
        return self._saida(aviso + verificada, "respondida", [f for f in fontes if f["n"] in usados], False, laudo, extra)


_padrao: Assistente | None = None


def responder(pergunta: str, historico: list[dict] | None = None) -> dict:
    """Ponto de integração com o front-end (04-frontend)."""
    global _padrao
    if _padrao is None:
        _padrao = Assistente()
    return _padrao.responder(pergunta, historico)
