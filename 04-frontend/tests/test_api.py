"""Testes da API e dos pipelines (pytest), sem subir a interface.

Rodar dentro de 04-frontend/: python -m pytest -q
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.append(str(Path(__file__).resolve().parents[1] / "frontend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app  # noqa: E402
from app.pipelines.triagem import triar  # noqa: E402
from app.providers import repositorio  # noqa: E402
from app.providers.llm import ErroLLM  # noqa: E402
from app.schemas.ocorrencia import RelatoEntrada  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    base = Path(__file__).resolve().parents[2] / "dados" / "ocorrencias.csv"
    monkeypatch.setattr(repositorio, "_repo",
                        repositorio.RepositorioCSV(base, tmp_path / "oc.csv"))
    return TestClient(app)


def _png(cor: int) -> bytes:
    b = io.BytesIO()
    Image.new("L", (64, 64), cor).save(b, "PNG")
    return b.getvalue()


# --- casos de teste da IA (mesmos da tabela do README) ---
CASOS = [
    ("Buraco enorme na avenida, uma moto caiu agora há pouco", "buraco", "alta"),
    ("Rachadura no muro da escola, parece que vai cair perto das crianças", "fissura", "alta"),
    ("Tem uma trinca pequena na calçada da praça", "fissura", "baixa"),
    ("Lâmpada do poste da minha rua está queimada", "outro", "baixa"),
]


@pytest.mark.parametrize("texto,tipo,prio", CASOS)
def test_triagem_regras(texto, tipo, prio):
    t = triar(RelatoEntrada(descricao=texto, bairro="Sé"), None)
    assert (t.tipo, t.prioridade, t.fonte) == (tipo, prio, "regras")


class LLMQuebrado:
    def json(self, *_):
        raise ErroLLM("timeout")


class LLMInvalido:
    def json(self, *_):
        return {"tipo": "dragão", "prioridade": "urgentíssima"}


class LLMBom:
    def json(self, *_):
        return {"tipo": "buraco", "prioridade": "alta", "confianca": 0.9, "resumo": "Buraco",
                "orientacao": "Sinalize o local.", "orgao_responsavel": "Subprefeitura"}


@pytest.mark.parametrize("llm,fonte", [(LLMQuebrado(), "regras"), (LLMInvalido(), "regras"),
                                       (LLMBom(), "llm")])
def test_triagem_degrada_sem_quebrar(llm, fonte):
    t = triar(RelatoEntrada(descricao="Buraco na rua principal", bairro="Sé"), llm)
    assert t.fonte == fonte


def test_fluxo_ponta_a_ponta(client):
    assert client.get("/health").json()["ok"]
    antes = len(client.get("/ocorrencias").json())
    relato = {"descricao": "Buraco grande na avenida perto do hospital", "bairro": "Sé"}
    tri = client.post("/triagem", json=relato).json()
    assert tri["prioridade"] == "alta"
    oc = client.post("/ocorrencias", json={"relato": relato, "tipo": tri["tipo"],
                                           "prioridade": "media", "confianca": 0.6}).json()
    assert oc["prioridade"] == "media"  # correção humana prevalece
    assert len(client.get("/ocorrencias").json()) == antes + 1
    up = client.patch(f"/ocorrencias/{oc['id']}", json={"status": "encaminhada"}).json()
    assert up["status"] == "encaminhada"
    assert len(client.get("/ocorrencias").json()) == antes + 1  # atualiza, não duplica


def test_validacao_entrada(client):
    assert client.post("/triagem", json={"descricao": "curto", "bairro": "Sé"}).status_code == 422
    assert client.post("/triagem", json={"descricao": "x" * 1001, "bairro": "Sé"}).status_code == 422
    assert client.patch("/ocorrencias/OC-9999", json={"status": "resolvida"}).status_code == 404
    assert client.patch("/ocorrencias/OC-0001", json={"status": "sumiu"}).status_code == 422


def test_visao_stub_e_formato(client):
    r = client.post("/visao", files={"foto": ("a.png", _png(10), "image/png")})
    assert r.status_code == 200 and r.json()["tipo"] == "buraco"
    r = client.post("/visao", files={"foto": ("a.txt", b"oi", "text/plain")})
    assert r.status_code == 415
    r = client.post("/visao", files={"foto": ("a.png", b"nao-e-imagem", "image/png")})
    assert r.status_code == 422


def test_chat_regras(client):
    r = client.post("/chat", json={"mensagem": "Tem um buraco na minha rua"}).json()
    assert r["sugestao_abrir_chamado"] is True
    assert client.post("/chat", json={"mensagem": ""}).status_code == 422


def test_cors_restritivo(client):
    r = client.options("/ocorrencias", headers={"Origin": "https://malicioso.example",
                                                "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers


def test_cliente_api_fora_do_ar():
    from providers.api_client import ClienteAPI, ErroAPI
    with pytest.raises(ErroAPI) as e:
        ClienteAPI("http://127.0.0.1:9", timeout=1).listar_ocorrencias()
    assert "Traceback" not in e.value.mensagem and "serviço" in e.value.mensagem
