"""Ponto de entrada do robô RPA CitizenTech.

Uso:
  python main.py                                   # dados de teste da disciplina
  python main.py --entrada ../dados/ocorrencias.csv  # base compartilhada do projeto
  python main.py --limpar                          # apaga saida/ antes (execução do zero)
"""
import argparse
import shutil
import sys
from pathlib import Path

from robo.pipeline import executar
from robo.util import BASE, SAIDA, carregar_env, configurar_log

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Robô RPA de encaminhamento de ocorrências urbanas")
    p.add_argument("--entrada", default=str(BASE / "dados_teste" / "ocorrencias_entrada.csv"))
    p.add_argument("--portal-url", default=None, help="URL da página de serviços (opcional)")
    p.add_argument("--limpar", action="store_true", help="apaga a pasta saida/ antes de rodar")
    a = p.parse_args()
    if a.limpar and SAIDA.exists():
        shutil.rmtree(SAIDA)
    carregar_env()
    configurar_log()
    rel = executar(Path(a.entrada), portal_url=a.portal_url)
    print("\n=== RELATÓRIO DA EXECUÇÃO ===")
    for k in ("lidas", "validas", "quarentena", "encaminhadas", "revisao", "ja_enviadas",
              "falhas", "fonte_destinos"):
        print(f"{k:>15}: {rel[k]}")
    print("Arquivos em:", SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
