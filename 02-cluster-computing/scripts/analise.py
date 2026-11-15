"""CitizenTech - Cluster Computing (GS 2026.2).

Dois modos:
  python scripts/analise.py estimar   -> estimativa teorica (NAO substitui o iSPD)
  python scripts/analise.py comparar  -> le resultados.csv (preenchido com o iSPD)
                                         e calcula reducao %, T2/T4 e balanceamento

Usa apenas a biblioteca padrao (Python 3.12).
"""
import csv
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Mesmos parametros de parametros.csv
N_TAREFAS = 1000
COMP_MIN, COMP_MED, COMP_MAX = 10_000, 65_000, 120_000  # MFlop
COMM_MED = 10            # Mbit
CAP_WORKER = 50_000      # MFlop/s
BANDA = 1000             # Mb/s
LATENCIA = 0.001         # s


def gerar_carga(seed: int = 42) -> list[tuple[float, float]]:
    """Carga sintetica aproximada (uniforme em torno da media). Mesma semente nos dois cenarios."""
    rnd = random.Random(seed)
    return [(rnd.uniform(COMP_MIN, COMP_MAX), COMM_MED) for _ in range(N_TAREFAS)]


def workqueue(carga, n_workers: int):
    """Simula Workqueue: o link do mestre envia uma tarefa por vez; worker livre pega a proxima."""
    livre = [0.0] * n_workers
    tarefas = [0] * n_workers
    mflop = [0.0] * n_workers
    link = 0.0  # instante em que o link do mestre fica livre
    for comp, comm in carga:
        w = min(range(n_workers), key=lambda i: livre[i])
        inicio_envio = max(link, livre[w])
        chegada = inicio_envio + comm / BANDA + LATENCIA
        link = chegada
        livre[w] = chegada + comp / CAP_WORKER
        tarefas[w] += 1
        mflop[w] += comp
    return max(livre), tarefas, mflop


def estimar():
    carga = gerar_carga()
    total = sum(c for c, _ in carga)
    print(f"Carga: {N_TAREFAS} tarefas, {total:,.0f} MFlop no total\n")
    res = {}
    for n in (2, 4, 8):
        t, tar, mf = workqueue(carga, n)
        res[n] = t
        ideal = total / (n * CAP_WORKER)
        print(f"{n} workers: makespan estimado = {t:8.1f} s (ideal sem comunicacao = {ideal:7.1f} s)")
        for i in range(n):
            print(f"   worker {i+1}: {tar[i]:4d} tarefas, {mf[i]:14,.0f} MFlop ({mf[i]/total:5.1%})")
    print(f"\nReducao estimada 2->4: {(1 - res[4]/res[2]):.1%} | T2/T4 = {res[2]/res[4]:.2f}")
    print("ATENCAO: estimativa de conferencia. Os numeros do relatorio devem vir do iSPD.")


def comparar():
    with open(BASE / "resultados.csv", encoding="utf-8") as f:
        linhas = {r["indicador"]: r for r in csv.DictReader(f)}
    try:
        t2 = float(linhas["total_simulated_time"]["cenario_A_2workers"])
        t4 = float(linhas["total_simulated_time"]["cenario_B_4workers"])
    except ValueError:
        sys.exit("Preencha total_simulated_time em resultados.csv com os valores do iSPD.")
    print(f"T2 = {t2:.2f} s | T4 = {t4:.2f} s")
    print(f"Reducao percentual = (T2 - T4)/T2 = {(t2 - t4) / t2:.1%}")
    print(f"Speedup T2/T4 = {t2 / t4:.2f} (ideal = 2,00) | eficiencia = {t2 / t4 / 2:.1%}")
    for col, n in (("cenario_A_2workers", 2), ("cenario_B_4workers", 4)):
        vals = []
        for i in range(1, n + 1):
            v = linhas[f"mflop_processado_worker_{i}"][col]
            if v and v != "-":
                vals.append(float(v))
        if len(vals) == n:
            media = sum(vals) / n
            print(f"{n} workers: desbalanceamento (max/media) = {max(vals) / media:.3f}")


if __name__ == "__main__":
    {"estimar": estimar, "comparar": comparar}.get(
        sys.argv[1] if len(sys.argv) > 1 else "estimar", estimar)()
