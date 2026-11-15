"""Testes com dados de teste: casos normais e casos de FALHA tratada. Rodar: pytest -q"""
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from robo import api, ia, ingestao, privacidade, scraping  # noqa: E402
from robo.pipeline import executar  # noqa: E402

DADOS = Path(__file__).resolve().parent.parent / "dados_teste"


def test_anonimiza_cpf_email_telefone():
    t = "CPF 123.456.789-09, fone (11) 98765-4321, mail a.b@x.com"
    out = privacidade.anonimizar(t)
    assert "123.456" not in out and "98765" not in out and "@" not in out
    assert "[CPF]" in out and "[TELEFONE]" in out and "[EMAIL]" in out


def test_quarentena_de_dados_invalidos():
    df = ingestao.ler_ocorrencias(DADOS / "ocorrencias_entrada.csv")
    validos, invalidos = ingestao.validar(df)
    assert len(validos) == 25 and len(invalidos) == 6
    motivos = " ".join(invalidos["motivo_invalido"])
    for m in ("id inválido", "duplicado", "coordenada", "data inválida", "origem inválida"):
        assert m in motivos


def test_arquivo_ausente_nao_quebra():
    df = ingestao.ler_ocorrencias(Path("nao_existe.csv"))
    assert df.empty and list(df.columns) == ingestao.COLUNAS


def test_ia_tipo_e_prioridade():
    r = ia.classificar({"descricao": "Buraco enorme na frente da escola", "origem": "chat"})
    assert r["tipo_ia"] == "buraco" and r["prioridade_ia"] == "alta" and not r["revisao_humana"]
    r = ia.classificar({"descricao": "Poste apagado", "origem": "chat"})
    assert r["tipo_ia"] == "outro" and r["revisao_humana"]  # robô não decide sozinho


def test_ia_respeita_modelo_de_visao_confiante():
    r = ia.classificar({"descricao": "foto", "tipo": "fissura", "origem": "visao", "confianca": 0.9})
    assert r["tipo_ia"] == "fissura"


def test_scraping_ok_e_layout_quebrado():
    d, fonte = scraping.obter_destinos(arquivo=DADOS / "portal_prefeitura.html")
    assert d["fissura"]["email"].startswith("defesacivil") and fonte != "padrao"
    d, fonte = scraping.obter_destinos(arquivo=DADOS / "nao_existe.html")
    assert fonte == "padrao" and "buraco" in d


def test_scraping_site_fora_do_ar(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    d, fonte = scraping.obter_destinos(url="http://127.0.0.1:9/fora-do-ar")
    assert fonte == "padrao"


def test_api_falha_usa_caminho_seguro(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "SAIDA", tmp_path)
    monkeypatch.setattr("time.sleep", lambda s: None)

    def boom(*a, **k):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(api.requests, "get", boom)
    assert api.feriados(2030) == set()


def test_dias_uteis_pula_fim_de_semana_e_feriado():
    # sexta 2026-11-13 + 1 dia útil = segunda 16; com feriado em 16 -> terça 17
    assert api.somar_dias_uteis(date(2026, 11, 13), 1, set()) == date(2026, 11, 16)
    assert api.somar_dias_uteis(date(2026, 11, 13), 1, {date(2026, 11, 16)}) == date(2026, 11, 17)


def test_pipeline_ponta_a_ponta_idempotente(tmp_path, monkeypatch):
    monkeypatch.setenv("ROBO_OFFLINE", "1")
    monkeypatch.setattr(api, "SAIDA", tmp_path)
    db = tmp_path / "t.db"
    r1 = executar(DADOS / "ocorrencias_entrada.csv", db=db, saida=tmp_path)
    assert r1["encaminhadas"] == 20 and r1["revisao"] == 5 and r1["falhas"] == 0
    r2 = executar(DADOS / "ocorrencias_entrada.csv", db=db, saida=tmp_path)
    assert r2["encaminhadas"] == 0 and r2["ja_enviadas"] == 20
    # nenhum dado pessoal sai no e-mail
    emails = " ".join(p.read_text(encoding="utf-8", errors="ignore")
                      for p in (tmp_path / "outbox").glob("*.eml"))
    assert "123.456.789-09" not in emails and "joao.silva@email.com" not in emails
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM execucoes").fetchone()[0] == 2
    assert (tmp_path / "quarentena.csv").exists() and (tmp_path / "revisao_humana.csv").exists()
    con.close()


def test_pipeline_entrada_ausente(tmp_path, monkeypatch):
    monkeypatch.setenv("ROBO_OFFLINE", "1")
    r = executar(tmp_path / "x.csv", db=tmp_path / "t.db", saida=tmp_path)
    assert r["lidas"] == 0 and r["falhas"] == 0
    assert isinstance(pd.read_json(tmp_path / "relatorio_execucao.json", typ="series"), pd.Series)
