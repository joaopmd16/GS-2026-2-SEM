"""Avalia o LLM com as 30 perguntas (20 do tema, sendo 5 de continuação, e 5 fora do escopo).
Uso: python testes/avaliar_llm.py extrativo qwen2.5:3b llama3.2:3b
Critério automático: a resposta contém as palavras-chave esperadas (| = todas),
ou, para fora do escopo, é uma recusa. Revisar manualmente a coluna 'correta_manual'."""
import csv, sys, time, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistente.kb import Buscador, construir
from assistente.llm import ExtrativoLLM, OllamaLLM, Memoria, ollama_disponivel

RAIZ = Path(__file__).resolve().parent.parent
MARCAS_RECUSA = ["só posso ajudar", "não posso", "desculpe", "fora", "procure", "defensoria",
                 "unidade de saúde", "não sei"]

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

def avaliar(nome_modelo, busc):
    llm = ExtrativoLLM(busc) if nome_modelo == "extrativo" else OllamaLLM(busc, nome_modelo)
    linhas = list(csv.DictReader(open(RAIZ / "testes/perguntas_llm.csv", encoding="utf-8")))
    memorias, res = {}, []
    for r in linhas:
        mem = memorias.setdefault(r["conversa"], Memoria())
        t = time.perf_counter(); resp = llm.responder(r["pergunta"], mem); dt = time.perf_counter() - t
        if r["palavras_chave"] == "RECUSA":
            ok = any(norm(m) in norm(resp) for m in MARCAS_RECUSA)
        else:
            ok = all(norm(k) in norm(resp) for k in r["palavras_chave"].split("|"))
        res.append({**r, "modelo": llm.nome, "resposta": resp, "correta_auto": int(ok),
                    "correta_manual": "", "latencia_s": round(dt, 3)})
    return res

if __name__ == "__main__":
    modelos = sys.argv[1:] or ["extrativo"]
    secoes, _ = construir(RAIZ / "base_conhecimento/documentos")
    busc = Buscador(secoes)
    resumo = []
    for m in modelos:
        if m != "extrativo" and not ollama_disponivel():
            print(f"[pulado] {m}: Ollama não está rodando"); continue
        res = avaliar(m, busc)
        nome = m.replace(":", "_")
        with open(RAIZ / f"evidencias/llm_respostas_{nome}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        def pct(tipo):
            sub = [x for x in res if x["tipo"] in tipo]
            return 100 * sum(x["correta_auto"] for x in sub) / len(sub)
        lin = {"modelo": m, "acerto_tema_%": round(pct({"tema", "continuacao"}), 1),
               "acerto_continuacao_%": round(pct({"continuacao"}), 1),
               "recusas_adequadas_%": round(pct({"fora_escopo"}), 1),
               "acerto_geral_%": round(pct({"tema", "continuacao", "fora_escopo"}), 1),
               "latencia_media_s": round(sum(x["latencia_s"] for x in res) / len(res), 3)}
        resumo.append(lin); print(lin)
    if resumo:
        with open(RAIZ / "evidencias/llm_resumo.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=resumo[0].keys()); w.writeheader(); w.writerows(resumo)
