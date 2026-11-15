"""Testes unitários (adaptação para fala, corpus e limites). Rodar: python -m pytest testes -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistente.fala import adaptar_para_fala as f  # noqa: E402
from assistente.kb import Buscador, construir, limpar  # noqa: E402
from assistente.llm import ExtrativoLLM, Memoria  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "base_conhecimento" / "documentos"


def test_markdown_e_emoji():
    s = f("## Prazo\n- **Até 10 dias** 😀")
    assert "#" not in s and "*" not in s and "😀" not in s


def test_numeros_e_telefone():
    s = f("Ligue 156 em até 3 dias.")
    assert "um cinco seis" in s and "três dias" in s


def test_valor_data_hora():
    s = f("Multa de R$ 1.500,00 em 19/11/2026 às 7h30.")
    assert "mil e quinhentos reais" in s and "dezenove de novembro" in s and "sete horas e trinta" in s


def test_protocolo_e_sigla():
    s = f("Seu protocolo é OC-0015, conforme a LGPD.")
    assert "O C zero zero um cinco" in s and "L G P D" in s


def test_concordancia_feminino():
    assert "setenta e duas horas" in f("Atendido em até 72 horas.")


def test_frases_curtas():
    assert all(len(x.split()) <= 23 for x in f(" ".join(["palavra"] * 60) + ".").split("."))


def test_limpeza_remove_ruido():
    t = limpar("Texto   com  espaços\n\n\n\nPágina 1 de 3\n© Prefeitura")
    assert t == "Texto com espaços"


def test_tres_corpus():
    _, c = construir(DOCS)
    assert set(c) == {"texto_puro", "perguntas_respostas", "conversacional"}
    assert all(len(v) > 0 for v in c.values())


def test_memoria_e_recusa():
    llm = ExtrativoLLM(Buscador(construir(DOCS)[0]))
    m = Memoria()
    llm.responder("Como peço a troca da lâmpada do poste?", m)
    assert "3 dias" in llm.responder("E qual é o prazo?", m)  # continuação resolve o tema
    assert m.ultimo_servico.lower().startswith("ilumina")
    assert "só posso ajudar" in llm.responder("Qual a cotação do dólar?", Memoria())
