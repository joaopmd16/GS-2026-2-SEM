# Relatório técnico — Zeladora, assistente de voz PT-BR
_GS 2026.2 · NLP, Chatbots & Virtual Agents · FIAP 2TIAP — Integrantes: (nomes e RMs)_

> Modelo para exportar em PDF (por exemplo `pandoc relatorio.md -o relatorio.pdf`). Os campos **[preencher]** dependem dos testes com pessoas reais.

## 1. Problema e persona
Os canais de zeladoria dependem de leitura e digitação. A persona Dona Cida (71 anos, baixa visão) não consegue registrar uma calçada quebrada. A solução é um assistente **de voz**: ela fala o problema e recebe a orientação falada. ODS 11 e 10.

## 2. Arquitetura
STT (faster-whisper, local) → LLM (Ollama qwen2.5:3b / llama3.2:3b) com prompt de sistema, memória de 6 turnos e base de conhecimento (BM25 + contexto no prompt) → adaptação para fala (números, datas, R$, siglas, frases curtas) → TTS (edge-tts FranciscaNeural; Piper offline). Interface Gradio com consentimento. Detalhes e justificativas no `README.md`.

## 3. Base de conhecimento e corpus
7 documentos simulados (txt, md, html com ruído) → limpeza → 28 seções → 3 corpus: texto puro (7), perguntas e respostas (40) e conversacional (10, com recusas). Escolhemos o RAG leve em vez do fine-tuning porque as regras mudam, porque reduz a alucinação e porque os corpus ficam prontos para um fine-tuning futuro.

## 4. Testes e resultados
### 4.1 STT — WER (20 áudios, ≥3 vozes, 5 com ruído)
| Modelo | WER geral | Limpo | Ruído | V1 | V2 | V3 | s/áudio |
|---|---|---|---|---|---|---|---|
| whisper base | [preencher] | | | | | | |
| whisper small | [preencher] | | | | | | |
Smoke test sintético: tiny em CPU, WER 0,0, 0,39 s/áudio (`evidencias/stt_smoke_sintetico.csv`).

### 4.2 LLM — 30 perguntas (20 no tema, 5 de continuação, 5 fora do escopo)
| Modelo | Acerto no tema | Continuação | Recusa correta | Latência média |
|---|---|---|---|---|
| extrativo-bm25 (baseline) | 100% | 5/5 | 5/5 | < 1 ms |
| qwen2.5:3b | [preencher] | | | |
| llama3.2:3b | [preencher] | | | |
_Ressalva: o baseline foi ajustado com estas mesmas perguntas._

### 4.3 TTS — 10 respostas, 3 avaliadores (1–5)
| Critério | Média |
|---|---|
| Naturalidade | [preencher] |
| Clareza | [preencher] |
| Pronúncia de números e siglas | [preencher] |

### 4.4 Ponta a ponta — 10 conversas × 3 turnos
Modo texto + TTS real: latência até a fala de 1,42 s (TTS 1,42 s, LLM < 1 ms). Com áudio e Ollama: **[preencher]** (`conversas_e2e.py --llm qwen2.5:3b --audio`).

## 5. Comparação de duas opções
- **LLM:** qwen2.5:3b × llama3.2:3b (qualidade em PT-BR, recusa, latência) → [conclusão].
- **STT:** whisper base × small (WER × latência em CPU) → [conclusão].

## 6. Ética e LGPD
Resumo de `docs/lgpd_etica.md`: consentimento, áudio apagado, log sem conteúdo, limites (saúde, jurídico, emergência), "não sei" no lugar da alucinação, sem clonagem de voz e análise de viés do STT por locutor e ruído.

## 7. Limitações e próximos passos
Documentos simulados; os testes com voz real ficam com o grupo; o edge-tts depende de rede. Próximos passos: fine-tuning com os corpus gerados, abertura real da ocorrência via API do módulo 01, barge-in e streaming de TTS.

## 8. Referências
Radford et al. (2022), *Whisper*; faster-whisper/CTranslate2; Qwen2.5 Technical Report; Llama 3.2 model card; Lei 13.709/2018 (LGPD); jiwer.
