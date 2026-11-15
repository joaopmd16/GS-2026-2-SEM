"""Demo: fila de inspeções CitizenTech como QUBO — clássico (força bruta + guloso) vs QAOA simulado.

Problema: escolher quais ocorrências a equipe inspeciona hoje, maximizando o
valor (prioridade x confiança da IA) sem estourar a capacidade (horas da equipe)
e penalizando pares de ocorrências distantes entre si (deslocamento).
QAOA é simulado em vetor de estado com NumPy puro (sem hardware, sem Qiskit).
Executar:  python demo_qaoa.py
"""
import itertools, math, time
import numpy as np

rng = np.random.default_rng(42)
PESO = {"alta": 3, "media": 2, "baixa": 1}

# Ocorrências sintéticas no formato do contrato de dados (dados/ocorrencias.csv)
OCORR = [
    ("OC-0001", "buraco",  "alta",  0.91, -23.5505, -46.6333, 2.0),
    ("OC-0002", "fissura", "media", 0.78, -23.5614, -46.6559, 1.5),
    ("OC-0003", "buraco",  "alta",  0.85, -23.5480, -46.6390, 2.0),
    ("OC-0004", "fissura", "baixa", 0.66, -23.5900, -46.6800, 1.0),
    ("OC-0005", "outro",   "media", 0.72, -23.5530, -46.6350, 1.5),
    ("OC-0006", "buraco",  "alta",  0.95, -23.6000, -46.6200, 2.5),
    ("OC-0007", "fissura", "media", 0.80, -23.5450, -46.6420, 1.0),
    ("OC-0008", "buraco",  "baixa", 0.60, -23.5700, -46.6900, 1.0),
]
N = len(OCORR)
CAP = 6.0  # horas disponíveis da equipe no dia

def km(a, b):
    return 111 * math.hypot(a[4] - b[4], (a[5] - b[5]) * math.cos(math.radians(23.5)))

valor = np.array([PESO[o[2]] * o[3] for o in OCORR])
horas = np.array([o[6] for o in OCORR])
dist = np.array([[km(a, b) for b in OCORR] for a in OCORR])
LAMBDA_CAP, LAMBDA_DIST = 1.5, 0.08

def custo(x):
    """Energia QUBO (menor = melhor)."""
    x = np.asarray(x)
    excesso = max(0.0, horas @ x - CAP)
    return -valor @ x + LAMBDA_CAP * excesso ** 2 + LAMBDA_DIST * (x @ dist @ x) / 2

# ---------- Clássico ----------
t = time.perf_counter()
estados = np.array(list(itertools.product([0, 1], repeat=N)))
energias = np.array([custo(s) for s in estados])
ot = estados[energias.argmin()]
t_bf = time.perf_counter() - t

x_g = np.zeros(N, int)
for i in np.argsort(-valor / horas):
    if horas @ x_g + horas[i] <= CAP:
        x_g[i] = 1

# ---------- QAOA simulado (vetor de estado) ----------
# Índice do estado de base: bit i -> qubit i. energias está na ordem de itertools.product
# (bit 0 mais significativo); usamos a mesma ordem para o vetor de estado.
def rx_all(psi, beta):
    psi = psi.reshape([2] * N)
    c, s = math.cos(beta), -1j * math.sin(beta)
    for q in range(N):
        a, b = np.take(psi, 0, axis=q), np.take(psi, 1, axis=q)
        psi = np.stack([c * a + s * b, s * a + c * b], axis=q)
    return psi.reshape(-1)

def qaoa(params):
    p = len(params) // 2
    psi = np.full(2 ** N, 2 ** (-N / 2), complex)
    E = (energias - energias.mean()) / energias.std()
    for k in range(p):
        psi = psi * np.exp(-1j * params[k] * E)
        psi = rx_all(psi, params[p + k])
    return np.abs(psi) ** 2

def esperado(params):
    return qaoa(params) @ energias

t = time.perf_counter()
P = 3
melhor = None
for _ in range(30):  # busca aleatória + refinamento simples (otimizador clássico do laço híbrido)
    x0 = rng.uniform(0, math.pi, 2 * P)
    f0 = esperado(x0)
    passo = 0.3
    for _ in range(150):
        cand = x0 + rng.normal(0, passo, 2 * P)
        fc = esperado(cand)
        if fc < f0:
            x0, f0 = cand, fc
        else:
            passo *= 0.98
    if melhor is None or f0 < melhor[1]:
        melhor = (x0, f0)
probs = qaoa(melhor[0])
t_q = time.perf_counter() - t
top = np.argsort(-probs)[:5]

def fmt(x):
    ids = [OCORR[i][0] for i in range(N) if x[i]]
    return f"{', '.join(ids)} | valor={valor @ x:.2f} horas={horas @ x:.1f} custo={custo(x):.3f}"

print(f"{N} ocorrências, {2**N} combinações possíveis, capacidade {CAP} h\n")
print(f"[Clássico exato] {fmt(ot)}   ({t_bf*1000:.1f} ms)")
print(f"[Clássico guloso] {fmt(x_g)}")
print(f"\n[QAOA simulado p={P}] tempo de simulação {t_q:.1f} s")
print(f"  P(ótimo) = {probs[energias.argmin()]:.3f}  (amostragem uniforme = {1/2**N:.3f})")
for r, i in enumerate(top, 1):
    print(f"  #{r} p={probs[i]:.3f}  {fmt(estados[i])}")
print("\nLeitura: em 8 variáveis o clássico vence fácil. O ponto é o crescimento 2^N:")
for n in (8, 30, 60, 300):
    print(f"  N={n:>3}: 2^N = {2.0**n:.2e} combinações")
