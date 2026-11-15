# 08 · NLP — **Zeladora**, assistente de voz da zeladoria urbana

Disciplina **NLP, Chatbots & Virtual Agents** (GS 2026.2 · FIAP 2TIAP) dentro da
**Plataforma CitizenTech de Zeladoria Urbana Acessível**.

O cidadão **fala** o problema da rua (buraco, calçada, poste apagado, árvore, entulho, bueiro)
e o assistente **responde falando**, sem que ninguém precise digitar.

## Problema, persona e ODS
- **Persona:** Dona Cida, 71 anos, baixa visão e pouca familiaridade com aplicativos. Ela quer avisar que a calçada da frente de casa está quebrada e saber quanto tempo demora o conserto.
- **Também atende:** pessoas com baixa alfabetização, deficiência visual ou motora, ou que estão com as mãos ocupadas.
- **Problema:** os canais de zeladoria dependem de formulários e de leitura. Quem tem mais dificuldade de acesso é justamente quem mais sofre com calçadas quebradas.
- **ODS:** 11 (cidades sustentáveis) e 10 (redução das desigualdades/acessibilidade).
- **Diferença para o módulo 05 (Generative AI):** o 05 é o chat **de texto** com RAG. Este módulo é o canal **de voz** para quem não consegue digitar ou ler.

## Arquitetura
```
🎤 microfone / upload ──▶ STT (faster-whisper, local) ──▶ LLM + memória + base de conhecimento ──▶ adaptação p/ fala ──▶ TTS (edge-tts) ──▶ 🔊
                         assistente/stt.py               assistente/llm.py + kb.py                   assistente/fala.py      assistente/tts.py
                                         └────────── assistente/pipeline.py (orquestra e mede a latência de cada etapa) ──────────┘
```
Cada etapa é uma classe separada com uma interface mínima (`transcrever()`, `responder()`,
`sintetizar()`). Trocar um componente não exige reescrever o resto: por exemplo, `PiperTTS`
no lugar de `EdgeTTS`, ou `ExtrativoLLM` no lugar de `OllamaLLM`.

| Etapa | Arquivo | Escolha | Por quê |
|---|---|---|---|
| Captura | `app.py` | Gradio `Audio` (microfone + upload) | Botão "apertar para falar" e envio de arquivo |
| STT | `assistente/stt.py` | faster-whisper `small` (int8 em CPU, float16 em GPU) | Local: a voz não sai da máquina (LGPD) |
| Base de conhecimento | `assistente/kb.py` | Documentos da Prefeitura → limpeza → seções → busca BM25 → contexto no prompt | Ver justificativa abaixo |
| LLM | `assistente/llm.py` | Ollama `qwen2.5:3b` (padrão) × `llama3.2:3b`; baseline `extrativo-bm25` | Pequeno, roda em máquina comum ou no Colab T4 |
| Memória | `Memoria` em `llm.py` | Janela de 6 turnos + tema do último turno | Resolve "e onde eu faço isso?" |
| Adaptação p/ fala | `assistente/fala.py` | Regras: sem markdown/emoji, números, datas, horas, R$, siglas, protocolo e frases curtas | O TTS lê o texto literalmente |
| TTS | `assistente/tts.py` | edge-tts `pt-BR-FranciscaNeural`; alternativa offline Piper `pt_BR-faber-medium` | Voz sintética pronta, sem clonagem |
| Interface | `app.py` | Gradio | Mostra a transcrição, a resposta em texto, o áudio e a latência |

### Base de conhecimento: por que contexto recuperado no prompt (RAG leve), e não só fine-tuning
- Os serviços e prazos da Prefeitura mudam. Basta trocar o documento em `base_conhecimento/documentos/`, sem treinar de novo.
- Respostas presas à fonte reduzem a alucinação. Se a busca não acha nada, o assistente **recusa** ou diz que **não sabe**.
- O mesmo pipeline **também gera os 3 corpus para fine-tuning** de uma LLM pequena (`corpus/`), como evolução futura:
  - `texto_puro.jsonl`: `{"text": ...}`, para pré-treino continuado no domínio.
  - `perguntas_respostas.jsonl`: `{"pergunta","resposta","servico","fonte"}`, para SFT de perguntas e respostas.
  - `conversacional.jsonl`: `{"messages":[system,user,assistant,...]}`, no formato chat, com perguntas de continuação e exemplos de recusa.

Formatos de entrada aceitos: `.txt`, `.md`, `.html`, `.pdf` e `.docx`. Os exemplos em
`base_conhecimento/documentos/` são **simulados** e trazem ruído de propósito (HTML com
menu/rodapé, espaços repetidos, "Página 1 de 1") para mostrar a limpeza.

### Nuvem ou local?
**Híbrido, priorizando o local.** O STT e o LLM rodam localmente: o áudio é dado pessoal e
biométrico, não há custo por uso e funciona sem internet boa. Só o **texto da resposta**
(sem dado do cidadão) vai para o edge-tts, porque a voz neural pt-BR dele é bem mais natural
que as opções offline. A latência do TTS fica em cerca de 1,4 s. Para rodar 100% offline,
troque por `PiperTTS`.

## Como rodar
```bash
cd 08-nlp
pip install -r requirements.txt
# LLM local (opcional, mas recomendado):
ollama pull qwen2.5:3b && ollama pull llama3.2:3b
python gerar_corpus.py            # base de conhecimento + 3 corpus em corpus/
python app.py                     # abre a interface (http://127.0.0.1:7860)
python app.py --llm extrativo     # sem Ollama (baseline)
```
**Google Colab (GPU T4):** `!pip install -r requirements.txt`, instale o Ollama
(`curl -fsSL https://ollama.com/install.sh | sh`, depois `ollama serve &` e `ollama pull qwen2.5:3b`)
e rode `python app.py --share`.

### Testes e métricas
```bash
python -m pytest testes -q                                   # testes unitários (9)
python testes/avaliar_llm.py extrativo qwen2.5:3b llama3.2:3b # 30 perguntas → evidencias/llm_*.csv
python testes/avaliar_stt.py base small                      # WER (jiwer) de 2 Whispers → evidencias/stt_*.csv
python testes/gerar_amostras_tts.py                          # 10 áudios → evidencias/tts/ + planilha
python testes/conversas_e2e.py --llm qwen2.5:3b [--audio]    # 10 conversas × 3 turnos → latência
```

## Evidências (geradas nesta máquina, sem GPU e sem Ollama)
| Teste | Resultado | Arquivo |
|---|---|---|
| Testes unitários | 9/9 passam | `testes/test_fala.py` |
| LLM baseline `extrativo-bm25`, 30 perguntas | 100% no tema (25/25, sendo 5/5 de continuação) e 100% de recusas (5/5) | `evidencias/llm_resumo.csv`, `llm_respostas_extrativo.csv` |
| Ponta a ponta, 10 conversas × 3 turnos (modo texto + TTS real) | TTS 1,42 s; LLM < 1 ms; total até a fala 1,42 s | `evidencias/e2e_extrativo-bm25.csv`, `latencia_log.csv` |
| 10 respostas sintetizadas | Áudios gerados; falta a nota de 3 avaliadores | `evidencias/tts/`, `testes/avaliacao_tts.csv` |
| Corpus | 28 seções → 7 de texto puro, 40 pares de pergunta e resposta, 10 conversas | `corpus/` |

⚠️ **Honestidade:** as regras de busca (sinônimos) foram ajustadas usando as mesmas 30
perguntas, então os 100% do baseline são otimistas. Para o relatório, faça uma rodada com
perguntas novas, ditas por outras pessoas.

### O que falta o grupo fazer (não dá para automatizar)
1. **Gravar os 20 áudios** de `testes/stt_roteiro.csv` em `testes/audios/` (`audio_01.wav`...), com **pelo menos 3 vozes** (V1, V2, V3...) e os **5 últimos com ruído de fundo** (TV, rua, ventilador). Preencha o `perfil_locutor` e depois rode `avaliar_stt.py base small`.
2. **Instalar o Ollama** e rodar `avaliar_llm.py extrativo qwen2.5:3b llama3.2:3b` (comparação entre modelos) e `conversas_e2e.py --llm qwen2.5:3b --audio`. Revise a coluna `correta_manual`.
3. **3 pessoas ouvem** `evidencias/tts/` e dão notas de 1 a 5 em `testes/avaliacao_tts.csv`.
4. Gerar o **relatório em PDF** a partir de `docs/relatorio.md` e gravar o **vídeo** seguindo `docs/roteiro_video.md`.

## Ética, segurança e LGPD
Ver `docs/lgpd_etica.md`. Resumo:
- Aviso e **consentimento obrigatório** (caixa de seleção) antes do primeiro uso.
- **Retenção mínima:** o áudio é apagado logo depois da transcrição (`stt.py`). O log de latência guarda só tempos e o tamanho da pergunta.
- **Limites:** recusa assuntos fora do tema. Saúde → 192 ou unidade de saúde; jurídico → Defensoria; emergência → 193/199.
- **Alucinação:** só responde com o contexto. Sem contexto, diz que não sabe e indica o 156.
- **Sem clonagem de voz:** só vozes sintéticas prontas.

## Modelos e licenças
| Componente | Modelo/versão | Licença |
|---|---|---|
| STT | faster-whisper ≥ 1.0.3 com Whisper `base` / `small` (OpenAI) | MIT |
| LLM | Qwen2.5-3B-Instruct (`qwen2.5:3b`) | Qwen Research License (uso não comercial no tamanho 3B) |
| LLM | Llama 3.2 3B Instruct (`llama3.2:3b`) | Llama 3.2 Community License |
| TTS | edge-tts ≥ 6.1, voz `pt-BR-FranciscaNeural` | edge-tts LGPL-3.0; voz pelos termos do serviço Microsoft |
| TTS offline | Piper `pt_BR-faber-medium` | MIT (Piper) / modelo CC |
| Interface | Gradio ≥ 4.44 | Apache-2.0 |
| Métrica | jiwer ≥ 3.0 | Apache-2.0 |

## Integração com os outros módulos
- **04-frontend:** pode importar `AssistenteVoz` e pôr a aba de voz na interface única.
- **05-generative-ai:** pode usar `corpus/` e `base_conhecimento/` como fonte compartilhada; este módulo cuida só do canal de voz.
- **01-rpa-ia:** o protocolo falado (`OC-0001`) segue o contrato **Ocorrência** do `CONTEXTO.md`, e o assistente orienta a consulta do status.
- **07-iot (OuviAí):** é complementar. O OuviAí atende surdos com alertas visuais; a Zeladora atende quem não lê ou não digita.

## Integrantes
_Preencher com os nomes completos e RMs._
