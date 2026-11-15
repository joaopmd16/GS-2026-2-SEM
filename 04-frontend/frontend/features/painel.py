"""Tela: painel de ocorrências (dados de dados/ocorrencias.csv via API) com filtros e Plotly."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from providers.api_client import ErroAPI
from state import session
from ui import components as ui

ORDEM_PRIO = ["alta", "media", "baixa"]


def filtros(df: pd.DataFrame, chave: str) -> pd.DataFrame:
    """Filtros reutilizados no painel público e na fila do gestor (chave evita conflito)."""
    c1, c2, c3 = st.columns(3)
    prio = c1.multiselect("Urgência", ORDEM_PRIO, default=ORDEM_PRIO, key=f"{chave}_prio",
                          format_func=lambda x: ui.PRIORIDADE[x][2].split(" —")[0])
    tipos = sorted(df["tipo"].unique())
    tipo = c2.multiselect("Tipo", tipos, default=tipos, key=f"{chave}_tipo",
                          format_func=lambda x: ui.TIPO.get(x, x))
    status = sorted(df["status"].unique())
    st_sel = c3.multiselect("Situação", status, default=status, key=f"{chave}_status",
                            format_func=ui.rotulo_status)
    return df[df["prioridade"].isin(prio) & df["tipo"].isin(tipo) & df["status"].isin(st_sel)]


def carregar() -> pd.DataFrame | None:
    try:
        with st.spinner("Carregando ocorrências…"):
            return session.ocorrencias_df()
    except ErroAPI as e:
        ui.erro_amigavel(e.mensagem)
        if st.button("Tentar de novo", key="retry_painel"):
            session.invalidar_ocorrencias()
            st.rerun()
        return None


def render() -> None:
    st.header("🗺️ Painel da cidade")
    df = carregar()
    if df is None:
        return
    if df.empty:
        ui.estado_vazio("Ainda não há ocorrências registradas.")
        return

    f = filtros(df, "painel")
    k = st.columns(4)
    ui.kpi(k[0], "Ocorrências", len(f))
    ui.kpi(k[1], "⛔ Alta urgência", int((f["prioridade"] == "alta").sum()))
    ui.kpi(k[2], "🏁 Resolvidas", int((f["status"] == "resolvida").sum()))
    ui.kpi(k[3], "Confiança média da IA", f"{f['confianca'].mean():.0%}" if len(f) else "—",
           "Média da confiança informada pelos modelos (visão/triagem).")
    if f.empty:
        ui.estado_vazio("Nenhuma ocorrência com esses filtros.", "Tente marcar mais opções.")
        return

    rot = f.assign(urgencia=f["prioridade"].map(lambda p: ui.PRIORIDADE[p][2].split(" —")[0]),
                   tipo_txt=f["tipo"].map(ui.TIPO))
    cores = {ui.PRIORIDADE[p][2].split(" —")[0]: c for p, c in ui.CORES_PRIORIDADE.items()}

    aba_mapa, aba_tempo, aba_tabela = st.tabs(["Mapa", "Linha do tempo", "Tabela"])
    with aba_mapa:
        fig = px.scatter_map(rot, lat="latitude", lon="longitude", color="urgencia",
                             color_discrete_map=cores, hover_name="id", hover_data={"tipo_txt": True, "bairro": True,
                                                          "status": True, "latitude": False,
                                                          "longitude": False},
                             zoom=10, height=420, labels={"urgencia": "Urgência",
                                                          "tipo_txt": "Tipo"})
        fig.update_traces(marker={"size": 14})
        fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Cores seguem a urgência, que também aparece escrita na legenda e no hover.")
    with aba_tempo:
        por_dia = (rot.assign(dia=rot["criado_em"].dt.date)
                   .groupby(["dia", "urgencia"]).size().reset_index(name="ocorrências"))
        fig = px.bar(por_dia, x="dia", y="ocorrências", color="urgencia",
                     color_discrete_map=cores, pattern_shape="urgencia",
                     labels={"dia": "Dia", "urgencia": "Urgência"})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Barras com hachura diferente por urgência (útil para daltonismo).")
    with aba_tabela:
        st.dataframe(rot[["id", "tipo_txt", "bairro", "urgencia", "status", "origem",
                          "confianca", "criado_em"]],
                     hide_index=True, use_container_width=True,
                     column_config={"confianca": st.column_config.ProgressColumn(
                         "Confiança", min_value=0, max_value=1, format="%.2f")})
