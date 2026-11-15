"""Tela: assistente conversacional (back-end usa o módulo 05-generative-ai quando existir)."""
from __future__ import annotations

import streamlit as st

from providers.api_client import ErroAPI
from state import session
from ui import components as ui


def _avaliar(i: int) -> None:
    ref = f"chat-{i}"
    fb = st.session_state.feedbacks
    if ref in fb:
        st.caption("Obrigado pela avaliação!" + (" 👍" if fb[ref] else " 👎"))
        return
    c1, c2, _ = st.columns([1, 1, 6])
    util = c1.button("👍 Útil", key=f"up{i}")
    ruim = c2.button("👎 Não ajudou", key=f"down{i}")
    if util or ruim:
        fb[ref] = bool(util)
        try:
            session.cliente().feedback(ref, bool(util))
        except ErroAPI:
            pass  # avaliação é opcional; não atrapalha o cidadão
        st.rerun()


def render() -> None:
    st.header("💬 Tire dúvidas com o assistente")
    st.caption("Respostas geradas por IA podem conter erros. Para emergências, ligue 190/193.")
    if not st.session_state.chat:
        ui.estado_vazio("Pergunte, por exemplo: “Como acompanho meu protocolo?” ou "
                        "“Tem um buraco na minha rua, o que faço?”")
    for i, m in enumerate(st.session_state.chat):
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m["role"] == "assistant":
                _avaliar(i)

    pergunta = st.chat_input("Escreva sua pergunta", max_chars=800)
    if not pergunta:
        return
    st.session_state.chat.append({"role": "user", "content": pergunta})
    with st.spinner("O assistente está pensando…"):
        try:
            r = session.cliente().conversar(pergunta, st.session_state.chat[:-1])
            texto = r["resposta"]
            if r.get("sugestao_abrir_chamado"):
                texto += "\n\n👉 Abra a aba **Reportar** para registrar o problema."
        except ErroAPI as e:
            texto = f"😕 {e.mensagem}"
    st.session_state.chat.append({"role": "assistant", "content": texto})
    st.rerun()
