# Roteiro do vídeo (máx. 5 min)

| Tempo | Cena | Fala / ação |
|---|---|---|
| 0:00–0:30 | Rosto do grupo + slide do problema | "A Dona Cida tem 71 anos e baixa visão. A calçada da casa dela está quebrada, mas o canal da Prefeitura é um formulário." ODS 10 e 11. |
| 0:30–1:15 | Diagrama da arquitetura (README) | Microfone → STT (faster-whisper local) → LLM + memória + base de conhecimento → adaptação para fala → TTS → alto-falante. Por que é local (LGPD). |
| 1:15–2:45 | **Demo ao vivo** no `app.py` | 1) marcar o consentimento; 2) falar "Tem um buraco enorme na minha rua, o que eu faço?"; 3) continuação: "E quanto tempo demora?"; 4) fora do escopo: "Qual a cotação do dólar?" (recusa); 5) emergência: "Uma árvore caiu no fio" (193/199). Mostrar a transcrição, o áudio e o painel de latência. |
| 2:45–3:30 | Base de conhecimento | Abrir um documento com ruído (`poda_arvore.html`), rodar `gerar_corpus.py`, mostrar os 3 corpus. |
| 3:30–4:20 | Resultados | Tabelas: WER por modelo/locutor/ruído; acerto das 30 perguntas (qwen × llama × extrativo); notas do TTS; latência média do e2e. |
| 4:20–5:00 | Ética e encerramento | Áudio apagado, sem clonagem, recusa em vez de alucinação, viés do STT. Limitações e próximos passos. |

**Dicas:** grave a tela em 1080p, use um microfone de headset, ensaie as falas da demo e mantenha o vídeo abaixo de 5:00.
