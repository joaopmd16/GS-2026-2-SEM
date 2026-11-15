"""OuviAí - cálculo do percentual de acerto e matriz de confusão.

Uso:
    python calcular_acerto.py validacao_ao_vivo.csv    # 15 tentativas ao vivo
    python calcular_acerto.py teste_arquivos.csv       # 15 WAVs de Test
    python calcular_acerto.py validacao_ao_vivo.csv --ocorrencias  # gera JSON p/ a plataforma

Preencha só a coluna `classe_prevista` (campainha | batida | ambiente | incerto).
A coluna `acerto` é recalculada automaticamente. Só a biblioteca padrão é usada.
"""
import csv, json, sys
from datetime import datetime, timezone

CLASSES = ["campainha", "batida", "ambiente"]

def carregar(caminho):
    with open(caminho, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    esp = "classe_esperada" if "classe_esperada" in linhas[0] else "classe_real"
    return linhas, esp

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    caminho = sys.argv[1]
    linhas, esp = carregar(caminho)
    preenchidas = [l for l in linhas if (l.get("classe_prevista") or "").strip()]
    if not preenchidas:
        print("Nenhuma linha com classe_prevista preenchida."); return
    previstas = CLASSES + ["incerto"]
    matriz = {r: {p: 0 for p in previstas} for r in CLASSES}
    acertos = 0
    for l in preenchidas:
        real, prev = l[esp].strip().lower(), l["classe_prevista"].strip().lower()
        if prev not in previstas: prev = "incerto"
        matriz[real][prev] += 1
        ok = real == prev
        l["acerto"] = "sim" if ok else "nao"
        acertos += ok
    n = len(preenchidas)
    print(f"Arquivo: {caminho}\nTentativas avaliadas: {n}/{len(linhas)}")
    print(f"Acertos: {acertos}  ->  Percentual de acerto = {acertos}/{n} = {100*acertos/n:.1f}%\n")
    print("Matriz de confusão (linha = real, coluna = prevista)")
    print(f"{'':>11}" + "".join(f"{p:>11}" for p in previstas))
    for r in CLASSES:
        print(f"{r:>11}" + "".join(f"{matriz[r][p]:>11}" for p in previstas))
    print("\nAcerto por classe:")
    for r in CLASSES:
        tot = sum(matriz[r].values())
        if tot: print(f"  {r:<10} {matriz[r][r]}/{tot} = {100*matriz[r][r]/tot:.0f}%")
    fp = sum(matriz[r]["ambiente"] for r in ["campainha", "batida"])
    fa = sum(matriz["ambiente"][p] for p in ["campainha", "batida"])
    print(f"\nFalsos positivos (ambiente classificado como evento): {fa}")
    print(f"Eventos perdidos (evento classificado como ambiente): {fp}")
    # grava a coluna acerto de volta
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)
    if "--ocorrencias" in sys.argv:
        ocs = []
        for i, l in enumerate(preenchidas, 1):
            prev = l["classe_prevista"].strip().lower()
            if prev not in ("campainha", "batida"): continue
            prob = float(l.get("probabilidade_exibida") or 0) or 0.0
            ocs.append({
                "id": f"OC-IOT-{i:04d}", "tipo": "alerta_sonoro", "origem": "iot",
                "descricao": f"Som detectado: {prev} (teste ao vivo OuviAí)",
                "confianca": round(prob, 2), "latitude": None, "longitude": None,
                "bairro": "", "prioridade": "baixa", "status": "aberta",
                "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        with open("integracao/ocorrencias_iot.json", "w", encoding="utf-8") as f:
            json.dump(ocs, f, ensure_ascii=False, indent=2)
        print(f"\n{len(ocs)} ocorrências gravadas em integracao/ocorrencias_iot.json")

if __name__ == "__main__":
    main()
