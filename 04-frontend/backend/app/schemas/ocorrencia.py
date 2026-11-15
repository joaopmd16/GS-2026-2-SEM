"""Modelos Pydantic — espelham o contrato de dados de CONTEXTO.md."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Tipo = Literal["fissura", "buraco", "alerta_sonoro", "outro"]
Origem = Literal["visao", "iot", "chat", "rpa"]
Prioridade = Literal["baixa", "media", "alta"]
Status = Literal["aberta", "encaminhada", "em_inspecao", "resolvida"]


class Ocorrencia(BaseModel):
    id: str
    tipo: Tipo
    origem: Origem
    descricao: str
    confianca: float = Field(ge=0, le=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    bairro: str
    prioridade: Prioridade
    status: Status
    criado_em: datetime


class RelatoEntrada(BaseModel):
    """Relato digitado pelo cidadão (entrada validada no back-end)."""
    descricao: str = Field(min_length=10, max_length=1000)
    bairro: str = Field(min_length=2, max_length=60)
    latitude: float = Field(default=-23.55, ge=-90, le=90)
    longitude: float = Field(default=-46.63, ge=-180, le=180)

    @field_validator("descricao", "bairro")
    @classmethod
    def limpar(cls, v: str) -> str:
        return " ".join(v.split())


class Triagem(BaseModel):
    """Saída ESTRUTURADA do LLM — nunca texto livre."""
    tipo: Tipo
    prioridade: Prioridade
    confianca: float = Field(ge=0, le=1)
    resumo: str = Field(max_length=200)
    orientacao: str = Field(max_length=400, description="O que o cidadão deve fazer agora")
    orgao_responsavel: str = Field(max_length=80)
    fonte: Literal["llm", "regras"] = "llm"


class ConfirmacaoEntrada(BaseModel):
    """Human-in-the-loop: cidadão confirma ou corrige a triagem antes de abrir o chamado."""
    relato: RelatoEntrada
    tipo: Tipo
    prioridade: Prioridade
    confianca: float = Field(ge=0, le=1)
    origem: Origem = "chat"


class AtualizarStatus(BaseModel):
    status: Status


class Feedback(BaseModel):
    referencia: str = Field(min_length=1, max_length=40)
    util: bool
    comentario: str = Field(default="", max_length=300)


class ChatEntrada(BaseModel):
    mensagem: str = Field(min_length=1, max_length=800)
    historico: list[dict] = Field(default_factory=list, max_length=20)


class ChatResposta(BaseModel):
    resposta: str
    sugestao_abrir_chamado: bool = False
    fonte: Literal["llm", "regras", "modulo_genai"] = "regras"


class DeteccaoVisao(BaseModel):
    tipo: Tipo
    confianca: float = Field(ge=0, le=1)
    explicacao: str
    fonte: Literal["modelo_visao", "stub"] = "stub"
