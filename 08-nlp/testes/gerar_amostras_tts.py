"""Sintetiza 10 respostas (já adaptadas para fala) para a avaliação de naturalidade
e clareza por 3 pessoas. Preenche a coluna texto_falado de testes/avaliacao_tts.csv."""
import csv
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistente.fala import adaptar_para_fala  # noqa: E402
from assistente.tts import EdgeTTS  # noqa: E402

RESPOSTAS = [
    "Você pode pedir o reparo pelo telefone 156 ou pelo aplicativo CitizenTech.",
    "O prazo é de até 10 dias úteis. Se houver risco de acidente, até 72 horas.",
    "A troca de lâmpada leva até 3 dias úteis e é gratuita.",
    "A conservação da calçada é do dono do imóvel. Se o dano for de raiz de árvore pública, a Prefeitura conserta.",
    "É proibido podar árvore na rua por conta própria. A multa pode chegar a R$ 1.500,00.",
    "Seu protocolo OC-0015 está em inspeção.",
    "A Central 156 atende de segunda a sábado, das 7h às 20h.",
    "Pequenos volumes de entulho, até 1 metro cúbico, podem ir de graça para um Ecoponto.",
    "Isso é uma emergência. Ligue agora 193 para os Bombeiros ou 199 para a Defesa Civil.",
    "Desculpe, eu só posso ajudar com serviços de zeladoria da cidade.",
]

raiz = Path(__file__).resolve().parent.parent
destino = raiz / "evidencias" / "tts"
destino.mkdir(parents=True, exist_ok=True)
tts = EdgeTTS()
planilha = raiz / "testes" / "avaliacao_tts.csv"
linhas = list(csv.DictReader(open(planilha, encoding="utf-8")))
for i, (txt, ln) in enumerate(zip(RESPOSTAS, linhas), 1):
    falado = adaptar_para_fala(txt)
    shutil.move(tts.sintetizar(falado), destino / f"resposta_{i:02d}.mp3")
    ln["texto_falado"] = falado
    print(i, falado)
with open(planilha, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=linhas[0].keys())
    w.writeheader()
    w.writerows(linhas)
