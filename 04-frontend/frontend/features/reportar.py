"""Tela: cidadão reporta um problema (texto + foto opcional) → IA tria → cidadão confirma."""
from __future__ import annotations

import streamlit as st

from providers.api_client import ErroAPI
from state import session
from ui import components as ui

# Coordenadas aproximadas do centro de cada bairro (dados mockados de São Paulo).
BAIRROS = {"Sé": (-23.5505, -46.6333), "Consolação": (-23.5614, -46.6559),
           "Bela Vista": (-23.5617, -46.6470), "Mooca": (-23.5596, -46.5996),
           "Pinheiros": (-23.5670, -46.6990), "Itaquera": (-23.5400, -46.4560),
           "Capão Redondo": (-23.6720, -46.7790), "Santana": (-23.5020, -46.6250)}
MAX_MB = 5


def _validar(descricao: str, bairro: str, foto) -> list[str]:
    erros = []
    if len(descricao.strip()) < 10:
        erros.append("Descreva o problema com pelo menos 10 caracteres.")
    if len(descricao) > 1000:
        erros.append("A descrição pode ter no máximo 1000 caracteres.")
    if not bairro:
        erros.append("Escolha o bairro.")
    if foto is not None and foto.size > MAX_MB * 1024 * 1024:
        erros.append(f"A foto passa de {MAX_MB} MB.")
    return erros


def _formulario() -> None:
    with st.form("form_relato", clear_on_submit=False):
        descricao = st.text_area(
            "O que está acontecendo? (obrigatório)", max_chars=1000, height=120,
            placeholder="Ex.: Buraco grande na faixa da direita, perto da escola.",
            help="Escreva com suas palavras. Não coloque nome, CPF ou telefone.")
        bairro = st.selectbox("Bairro (obrigatório)", list(BAIRROS), index=None,
                              placeholder="Escolha o bairro")
        foto = st.file_uploader("Foto do problema (opcional, JPG ou PNG até 5 MB)",
                                type=["jpg", "jpeg", "png"])
        enviar = st.form_submit_button("Analisar meu relato", type="primary")

    if not enviar:
        return
    erros = _validar(descricao, bairro, foto)
    if erros:
        for e in erros:
            st.warning(f"✏️ {e}")
        return

    api = session.cliente()
    lat, lon = BAIRROS[bairro]
    visao = None
    with st.status("Analisando seu relato…", expanded=True) as s:
        try:
            if foto is not None:
                st.write("📷 Olhando a foto…")
                visao = api.analisar_foto(foto.name, foto.getvalue(), foto.type)
            st.write("🧠 Entendendo a descrição e definindo a prioridade…")
            triagem = api.triar(descricao, bairro, lat, lon)
            s.update(label="Pronto! Revise abaixo antes de enviar.", state="complete")
        except ErroAPI as e:
            s.update(label="Não foi possível analisar agora.", state="error")
            ui.erro_amigavel(e.mensagem)
            return

    origem, tipo, conf = "chat", triagem["tipo"], triagem["confianca"]
    if visao and visao["tipo"] != "outro" and visao["confianca"] >= conf:
        origem, tipo, conf = "visao", visao["tipo"], visao["confianca"]
    st.session_state.triagem_pendente = {
        "relato": {"descricao": descricao, "bairro": bairro, "latitude": lat, "longitude": lon},
        "triagem": triagem, "visao": visao, "origem": origem, "tipo": tipo, "confianca": conf}
    st.rerun()  # mostra a etapa de revisão (human-in-the-loop)


def _revisao() -> None:
    """Human-in-the-loop: nada é enviado à prefeitura sem o OK do cidadão."""
    p = st.session_state.triagem_pendente
    t = p["triagem"]
    st.subheader("Confira o que a IA entendeu")
    if t["fonte"] == "regras":
        st.caption("ℹ️ Classificação feita pelo modo simplificado (a IA principal está "
                   "indisponível). Revise com atenção.")
    ui.selo_prioridade(t["prioridade"])
    st.markdown(f"**Resumo:** {t['resumo']}")
    st.markdown(f"**O que fazer agora:** {t['orientacao']}")
    st.markdown(f"**Quem vai cuidar:** {t['orgao_responsavel']}")
    ui.barra_confianca(p["confianca"])
    if p["visao"]:
        st.caption(f"📷 Foto: {p['visao']['explicacao']} "
                   f"({'modelo de visão' if p['visao']['fonte'] == 'modelo_visao' else 'análise simplificada'})")

    tipos = list(ui.TIPO)
    prios = ["alta", "media", "baixa"]
    with st.form("form_confirmar"):
        st.markdown("**Está certo? Você pode corrigir antes de enviar.**")
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo do problema", tipos, index=tipos.index(p["tipo"]),
                            format_func=ui.TIPO.get)
        prio = c2.selectbox("Urgência", prios, index=prios.index(t["prioridade"]),
                            format_func=lambda x: ui.PRIORIDADE[x][2])
        ok = st.form_submit_button("✅ Confirmar e enviar à prefeitura", type="primary")
        cancelar = st.form_submit_button("Cancelar")
    if cancelar:
        st.session_state.triagem_pendente = None
        st.rerun()
    if ok:
        corrigido = tipo != p["tipo"] or prio != t["prioridade"]
        with st.spinner("Registrando seu chamado…"):
            try:
                oc = session.cliente().confirmar(p["relato"], tipo, prio, p["confianca"],
                                                 p["origem"])
                if corrigido:  # correção humana vira sinal de qualidade para a IA
                    session.cliente().feedback(oc["id"], False,
                                               f"corrigido: {p['tipo']}/{t['prioridade']}"
                                               f" -> {tipo}/{prio}")
            except ErroAPI as e:
                ui.erro_amigavel(e.mensagem)
                return
        session.registrar_protocolo(oc)
        st.session_state.triagem_pendente = None
        st.toast(f"Chamado {oc['id']} registrado!", icon="✅")
        st.rerun()


def render() -> None:
    st.header("📣 Reportar um problema")
    st.write("Conte o que viu na rua. A IA sugere o tipo e a urgência, **você confere** e só "
             "então o chamado vai para a prefeitura.")
    if st.session_state.triagem_pendente:
        _revisao()
    else:
        _formulario()

    st.divider()
    st.subheader("Meus protocolos nesta visita")
    if not st.session_state.meus_protocolos:
        ui.estado_vazio("Você ainda não enviou nenhum relato.",
                        "Quando confirmar um relato, o protocolo aparece aqui.")
    for oc in st.session_state.meus_protocolos:
        ui.cartao_ocorrencia(oc)
