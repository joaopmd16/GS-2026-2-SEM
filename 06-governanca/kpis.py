"""KPIs da Plataforma CitizenTech (Business Analytics).

Lê a base compartilhada dados/ocorrencias.csv (contrato de dados do CONTEXTO.md)
e calcula os indicadores usados no relatório de Governança.

Uso:  python 06-governanca/kpis.py [caminho_csv]
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "dados" / "ocorrencias.csv"


def calcular(df: pd.DataFrame) -> dict:
    df["criado_em"] = pd.to_datetime(df["criado_em"])
    total = len(df)
    return {
        "total_ocorrencias": total,
        "por_origem": df["origem"].value_counts().to_dict(),
        "por_tipo": df["tipo"].value_counts().to_dict(),
        "por_status": df["status"].value_counts().to_dict(),
        "taxa_encaminhamento_%": round(100 * (df["status"] != "aberta").mean(), 1) if total else 0,
        "taxa_resolucao_%": round(100 * (df["status"] == "resolvida").mean(), 1) if total else 0,
        "pct_prioridade_alta_%": round(100 * (df["prioridade"] == "alta").mean(), 1) if total else 0,
        "confianca_media_visao": round(df.loc[df["origem"] == "visao", "confianca"].mean(), 3)
        if (df["origem"] == "visao").any() else None,
        "baixa_confianca_revisao_humana": int((df["confianca"] < 0.6).sum()),
        "ocorrencias_por_bairro": df["bairro"].value_counts().to_dict(),
    }


if __name__ == "__main__":
    dados = pd.read_csv(CSV)
    for chave, valor in calcular(dados).items():
        print(f"{chave}: {valor}")
