"""Orquestração do robô: entrada -> validação -> IA -> scraping -> API -> SQL -> e-mail -> relatório."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from . import api, banco, email_bot, ia, ingestao, scraping
from .util import SAIDA

log = logging.getLogger("robo")


def executar(entrada: Path, db: Path = SAIDA / "citizentech_rpa.db", saida: Path = SAIDA,
             portal_url: str | None = None) -> dict:
    inicio = datetime.now().isoformat(timespec="seconds")
    saida.mkdir(parents=True, exist_ok=True)
    rel = {"inicio": inicio, "lidas": 0, "validas": 0, "quarentena": 0, "encaminhadas": 0,
           "revisao": 0, "ja_enviadas": 0, "falhas": 0, "fonte_destinos": ""}

    df = ingestao.ler_ocorrencias(entrada)
    rel["lidas"] = len(df)
    validos, invalidos = ingestao.validar(df)
    rel["validas"], rel["quarentena"] = len(validos), len(invalidos)
    if len(invalidos):
        invalidos.drop(columns=["criado_dt"]).to_csv(saida / "quarentena.csv", index=False)

    destinos, rel["fonte_destinos"] = scraping.obter_destinos(portal_url)
    con = banco.conectar(db)
    revisao = []

    for row in validos.to_dict("records"):
        oid = row["id"]
        try:
            res = ia.classificar(row)
            o = {**row, "tipo": res["tipo_ia"], "prioridade": res["prioridade_ia"],
                 "confianca": res["confianca_ia"], "revisao_humana": int(res["revisao_humana"])}
            o.pop("criado_dt", None)
            dest = destinos.get(o["tipo"], destinos["outro"])
            dias = dest["prazo_dias"] if o["prioridade"] != "alta" else max(1, dest["prazo_dias"] // 2)
            o["prazo"] = api.somar_dias_uteis(row["criado_dt"].date(), dias).isoformat()
            o["orgao"] = dest["orgao"]

            if o["revisao_humana"]:
                o["status"] = "aberta"
                revisao.append({k: o[k] for k in ("id", "tipo", "confianca", "descricao")})
                rel["revisao"] += 1
                banco.salvar_ocorrencia(con, o)
                log.info("%s -> revisão humana (confiança %.2f)", oid, o["confianca"])
            elif banco.ja_enviado(con, oid):
                rel["ja_enviadas"] += 1
                log.info("%s já encaminhada anteriormente — não reenvia (idempotência)", oid)
            else:
                o["status"] = "encaminhada"
                arq = email_bot.enviar(o, dest, saida / "outbox")
                banco.salvar_ocorrencia(con, o)
                banco.registrar_envio(con, oid, dest["email"], arq)
                rel["encaminhadas"] += 1
                log.info("%s -> %s [%s, %s] prazo %s", oid, dest["orgao"], o["tipo"],
                         o["prioridade"], o["prazo"])
            con.commit()
        except Exception as e:  # um registro ruim não derruba o robô
            con.rollback()
            rel["falhas"] += 1
            log.exception("Falha ao processar %s: %s", oid, e)

    if revisao:
        import pandas as pd
        pd.DataFrame(revisao).to_csv(saida / "revisao_humana.csv", index=False)
    rel["fim"] = datetime.now().isoformat(timespec="seconds")
    banco.registrar_execucao(con, rel)
    con.commit()
    rel["por_bairro"] = banco.resumo_por_bairro(con)
    con.close()
    (saida / "relatorio_execucao.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    log.info("Fim: %s", {k: v for k, v in rel.items() if k != "por_bairro"})
    return rel
