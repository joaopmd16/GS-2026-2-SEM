from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..pipelines import chat as chat_pipe
from ..pipelines.triagem import triar
from ..providers.llm import obter_llm
from ..providers.modulos import detectar_dano
from ..providers.repositorio import obter_repositorio
from ..schemas.ocorrencia import (AtualizarStatus, ChatEntrada, ChatResposta, ConfirmacaoEntrada,
                                  DeteccaoVisao, Feedback, Ocorrencia, RelatoEntrada, Triagem)

router = APIRouter()
MAX_FOTO = 5 * 1024 * 1024
TIPOS_FOTO = {"image/jpeg", "image/png"}


@router.get("/health")
def health():
    return {"ok": True, "llm": obter_llm() is not None}


@router.get("/ocorrencias", response_model=list[Ocorrencia])
def listar():
    return obter_repositorio().listar()


@router.post("/triagem", response_model=Triagem)
def triagem(relato: RelatoEntrada):
    return triar(relato, obter_llm())


@router.post("/ocorrencias", response_model=Ocorrencia, status_code=201)
def confirmar(c: ConfirmacaoEntrada):
    """Só é chamado DEPOIS de o cidadão revisar/corrigir a triagem (human-in-the-loop)."""
    repo = obter_repositorio()
    o = Ocorrencia(id=repo.proximo_id(), tipo=c.tipo, origem=c.origem,
                   descricao=c.relato.descricao, confianca=c.confianca,
                   latitude=c.relato.latitude, longitude=c.relato.longitude,
                   bairro=c.relato.bairro, prioridade=c.prioridade, status="aberta",
                   criado_em=datetime.now().replace(microsecond=0))
    return repo.salvar(o)


@router.patch("/ocorrencias/{id_}", response_model=Ocorrencia)
def atualizar(id_: str, a: AtualizarStatus):
    repo = obter_repositorio()
    o = repo.obter(id_)
    if not o:
        raise HTTPException(404, "Ocorrência não encontrada.")
    return repo.salvar(o.model_copy(update={"status": a.status}))


@router.post("/visao", response_model=DeteccaoVisao)
async def visao(foto: UploadFile = File(...)):
    if foto.content_type not in TIPOS_FOTO:
        raise HTTPException(415, "Envie uma foto JPG ou PNG.")
    dados = await foto.read(MAX_FOTO + 1)
    if len(dados) > MAX_FOTO:
        raise HTTPException(413, "A foto passa de 5 MB.")
    try:
        tipo, conf, fonte = detectar_dano(dados)
    except Exception:
        raise HTTPException(422, "Não foi possível ler a imagem.")
    expl = {"buraco": "A imagem parece mostrar um buraco ou afundamento na via.",
            "fissura": "A imagem parece mostrar rachaduras ou fissuras."}.get(
        tipo, "Não identificamos um dano claro. Descreva o problema no texto.")
    return DeteccaoVisao(tipo=tipo, confianca=conf, explicacao=expl, fonte=fonte)


@router.post("/chat", response_model=ChatResposta)
def chat(e: ChatEntrada):
    return chat_pipe.responder(e, obter_llm())


@router.post("/feedback", status_code=204)
def feedback(f: Feedback):
    obter_repositorio().registrar_feedback(f.referencia, f.util, f.comentario)
