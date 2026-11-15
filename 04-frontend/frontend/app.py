"""CitizenTech — Zeladoria Urbana Acessível (front-end Streamlit).

Rodar dentro de frontend/: streamlit run app.py
Este arquivo só monta o layout; cada tela fica em features/.
"""
import streamlit as st

from features import chat, gestor, painel, reportar
from state import session
from ui import components as ui

st.set_page_config(page_title="CitizenTech — Zeladoria Acessível", page_icon="🏙️",
                   layout="wide")
session.iniciar()

with st.sidebar:
    st.title("🏙️ CitizenTech")
    st.write("Zeladoria urbana acessível: reporte, acompanhe e tire dúvidas — tudo por texto.")
    st.session_state.perfil = st.radio("Quem está usando?", ["Cidadão", "Gestor"],
                                       index=["Cidadão", "Gestor"].index(st.session_state.perfil),
                                       help="Gestor vê a fila e muda o status dos chamados.")
    st.session_state.alto_contraste = st.toggle("Alto contraste",
                                                value=st.session_state.alto_contraste)
    st.divider()
    saude = session.saude_api()
    if saude is None:
        st.error("🔴 Serviço indisponível no momento")
    elif saude.get("llm"):
        st.success("🟢 Serviço online · IA completa")
    else:
        st.warning("🟡 Serviço online · IA em modo simplificado")
    st.caption("Não informe nome, CPF ou telefone nos relatos (LGPD).")

ui.css_acessibilidade(st.session_state.alto_contraste)

abas = ["📣 Reportar", "💬 Assistente", "🗺️ Painel"]
if st.session_state.perfil == "Gestor":
    abas.append("🛠️ Gestor")
tabs = st.tabs(abas)
with tabs[0]:
    reportar.render()
with tabs[1]:
    chat.render()
with tabs[2]:
    painel.render()
if len(tabs) > 3:
    with tabs[3]:
        gestor.render()
