"""Tela do gestor (RBAC simples): fila priorizada e mudança de status (segundo HITL)."""
from __future__ import annotations

import streamlit as st

from features import painel
from providers.api_client import ErroAPI
from state import session
from ui import components as ui

PROXIMO = {"aberta": "encaminhada", "encaminhada": "em_inspecao", "em_inspecao": "resolvida"}


def render() -> None:
    st.header("🛠️ Fila do gestor")
    st.caption("A IA sugere a prioridade; o gestor decide o encaminhamento.")
    df = painel.carregar()
    if df is None:
        return
    pend = df[df["status"] != "resolvida"]
    if pend.empty:
        ui.estado_vazio("Nenhuma ocorrência pendente. 🎉")
        return
    pend = painel.filtros(pend, "gestor")
    pend = pend.assign(_o=pend["prioridade"].map({"alta": 0, "media": 1, "baixa": 2}))
    for _, oc in pend.sort_values(["_o", "criado_em"]).iterrows():
        oc = oc.to_dict()
        ui.cartao_ocorrencia(oc)
        prox = PROXIMO.get(oc["status"])
        if prox and st.button(f"Mover {oc['id']} para “{ui.rotulo_status(prox)}”",
                              key=f"mv_{oc['id']}"):
            try:
                session.cliente().atualizar_status(oc["id"], prox)
                session.invalidar_ocorrencias()
                st.toast(f"{oc['id']} atualizado.", icon="✅")
                st.rerun()
            except ErroAPI as e:
                ui.erro_amigavel(e.mensagem)
