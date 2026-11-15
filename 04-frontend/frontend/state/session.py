"""Estado centralizado (st.session_state) e cache (st.cache_*).

Toda leitura/escrita de estado passa por aqui, para não espalhar chaves mágicas pelas telas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from providers.api_client import ClienteAPI

PADROES = {
    "perfil": "Cidadão",          # Cidadão | Gestor (RBAC simples)
    "alto_contraste": False,
    "triagem_pendente": None,     # dict com relato + triagem aguardando confirmação (HITL)
    "meus_protocolos": [],        # histórico de relatos confirmados nesta sessão
    "chat": [],                   # [{"role": "user"|"assistant", "content": str}]
    "feedbacks": {},              # referência → útil?
}


def iniciar() -> None:
    for k, v in PADROES.items():
        if k not in st.session_state:
            st.session_state[k] = v.copy() if isinstance(v, (list, dict)) else v


@st.cache_resource
def cliente() -> ClienteAPI:
    """Uma única sessão HTTP por processo (reaproveita conexões entre reruns)."""
    return ClienteAPI()


@st.cache_data(ttl=60, show_spinner=False)
def ocorrencias_df() -> pd.DataFrame:
    """Lista de ocorrências com cache: filtros e reruns NÃO chamam a API de novo."""
    df = pd.DataFrame(cliente().listar_ocorrencias())
    if not df.empty:
        df["criado_em"] = pd.to_datetime(df["criado_em"])
    return df


@st.cache_data(ttl=15, show_spinner=False)
def saude_api() -> dict | None:
    try:
        return cliente().saude()
    except Exception:
        return None


def invalidar_ocorrencias() -> None:
    ocorrencias_df.clear()


def registrar_protocolo(oc: dict) -> None:
    st.session_state.meus_protocolos.insert(0, oc)
    invalidar_ocorrencias()
