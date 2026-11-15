"""Componentes visuais reutilizáveis.

Regra de acessibilidade: cor NUNCA sozinha — sempre cor + ícone + texto.
Paleta com contraste ≥ 4.5:1 sobre branco (WCAG AA).
"""
from __future__ import annotations

import html

import streamlit as st

PRIORIDADE = {  # cor de fundo, ícone, rótulo
    "alta": ("#B42318", "⛔", "Prioridade ALTA — risco a pessoas"),
    "media": ("#B54708", "⚠️", "Prioridade MÉDIA"),
    "baixa": ("#067647", "✅", "Prioridade BAIXA"),
}
STATUS = {
    "aberta": ("📥", "Aberta"),
    "encaminhada": ("📨", "Encaminhada à prefeitura"),
    "em_inspecao": ("🔎", "Em inspeção"),
    "resolvida": ("🏁", "Resolvida"),
}
TIPO = {"buraco": "🕳️ Buraco", "fissura": "🧱 Fissura/rachadura",
        "alerta_sonoro": "🔔 Alerta sonoro", "outro": "📌 Outro"}
CORES_PRIORIDADE = {k: v[0] for k, v in PRIORIDADE.items()}


def selo_prioridade(prioridade: str, compacto: bool = False) -> None:
    cor, icone, rotulo = PRIORIDADE.get(prioridade, ("#475467", "❔", "Sem prioridade"))
    texto = rotulo.split(" —")[0] if compacto else rotulo
    st.markdown(
        f'<span role="status" aria-label="{html.escape(rotulo)}" style="background:{cor};'
        f'color:#fff;padding:4px 10px;border-radius:999px;font-weight:600;">'
        f'{icone} {html.escape(texto)}</span>', unsafe_allow_html=True)


def rotulo_status(status: str) -> str:
    icone, txt = STATUS.get(status, ("❔", status))
    return f"{icone} {txt}"


def barra_confianca(confianca: float, rotulo: str = "Confiança da IA") -> None:
    nivel = "alta" if confianca >= 0.75 else "moderada" if confianca >= 0.5 else "baixa"
    st.progress(min(max(confianca, 0.0), 1.0), text=f"{rotulo}: {confianca:.0%} ({nivel})")
    if confianca < 0.5:
        st.caption("⚠️ A IA está pouco segura. Revise com atenção antes de confirmar.")


def cartao_ocorrencia(oc: dict, mostrar_descricao: bool = True) -> None:
    """Usado no histórico do cidadão, no painel e na fila do gestor."""
    with st.container(border=True):
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**{html.escape(oc['id'])}** · {TIPO.get(oc['tipo'], oc['tipo'])} · "
                    f"{html.escape(str(oc['bairro']))}")
        with c2:
            selo_prioridade(oc["prioridade"], compacto=True)
        if mostrar_descricao:
            st.write(oc["descricao"])
        st.caption(f"{rotulo_status(oc['status'])} · origem: {oc['origem']} · "
                   f"{str(oc['criado_em'])[:16].replace('T', ' ')}")


def estado_vazio(mensagem: str, dica: str = "") -> None:
    st.info(f"🗂️ {mensagem}" + (f"\n\n{dica}" if dica else ""))


def erro_amigavel(mensagem: str) -> None:
    st.error(f"😕 {mensagem}", icon=None)


def kpi(col, titulo: str, valor, ajuda: str = "") -> None:
    col.metric(titulo, valor, help=ajuda or None)


def css_acessibilidade(alto_contraste: bool) -> None:
    base = """
    <style>
      html, body, [class*="css"] { font-size: 17px; }
      :focus-visible { outline: 3px solid #1D4ED8 !important; outline-offset: 2px; }
      .stButton button { min-height: 44px; }  /* alvo de toque ≥ 44px */
    </style>"""
    contraste = """
    <style>
      .stApp { background:#000 !important; color:#fff !important; }
      .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp li
        { color:#fff !important; }
      .stButton button { background:#FFD60A !important; color:#000 !important;
        border:2px solid #fff !important; }
    </style>"""
    st.markdown(base + (contraste if alto_contraste else ""), unsafe_allow_html=True)
