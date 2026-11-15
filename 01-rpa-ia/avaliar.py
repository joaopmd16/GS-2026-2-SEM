"""Avaliação da IA num conjunto rotulado (dados_teste/rotulos.csv) -> evidencias/avaliacao.md"""
import sys

import pandas as pd

from robo import ia, ingestao
from robo.util import BASE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

entrada = ingestao.ler_ocorrencias(BASE / "dados_teste" / "ocorrencias_entrada.csv")
validos, _ = ingestao.validar(entrada)
rot = pd.read_csv(BASE / "dados_teste" / "rotulos.csv")
df = validos.merge(rot, on="id")
pred = pd.DataFrame([ia.classificar(r) for r in df.to_dict("records")], index=df.index)
df = pd.concat([df, pred], axis=1)

n = len(df)
auto = df[~df["revisao_humana"]]
acc_tipo = (df["tipo_ia"] == df["tipo_real"]).mean()
acc_prio = (df["prioridade_ia"] == df["prioridade_real"]).mean()
acc_tipo_auto = (auto["tipo_ia"] == auto["tipo_real"]).mean()
erros = df[(df["tipo_ia"] != df["tipo_real"]) | (df["prioridade_ia"] != df["prioridade_real"])]

linhas = [
    "# Avaliação da IA (classificador de tipo e prioridade)\n",
    f"Amostra: **{n} ocorrências sintéticas rotuladas manualmente** (`dados_teste/rotulos.csv`).\n",
    "| Métrica | Resultado |", "|---|---|",
    f"| Acurácia tipo (todas) | {acc_tipo:.0%} ({(df['tipo_ia'] == df['tipo_real']).sum()}/{n}) |",
    f"| Acurácia prioridade (todas) | {acc_prio:.0%} ({(df['prioridade_ia'] == df['prioridade_real']).sum()}/{n}) |",
    f"| Enviadas p/ revisão humana | {int(df['revisao_humana'].sum())}/{n} |",
    f"| Acurácia tipo só nas decididas automaticamente | {acc_tipo_auto:.0%} ({len(auto)} casos) |",
    "\n## Matriz de confusão — tipo\n",
    pd.crosstab(df["tipo_real"], df["tipo_ia"], rownames=["real"], colnames=["previsto"]).to_markdown(),
    "\n## Matriz de confusão — prioridade\n",
    pd.crosstab(df["prioridade_real"], df["prioridade_ia"], rownames=["real"], colnames=["previsto"]).to_markdown(),
    "\n## Erros (para análise)\n",
    erros[["id", "descricao", "tipo_real", "tipo_ia", "prioridade_real", "prioridade_ia",
           "revisao_humana"]].to_markdown(index=False),
]
texto = "\n".join(linhas) + "\n"
(BASE / "evidencias").mkdir(exist_ok=True)
(BASE / "evidencias" / "avaliacao.md").write_text(texto, encoding="utf-8")
print(texto)
