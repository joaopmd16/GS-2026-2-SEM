# 05 — Generative AI & Advanced Nets · Assistente Conversacional CitizenTech (RAG)

> GS 2026.2 · FIAP · 2TIAP. **Integrantes:** _preencher nome completo e RM (até 3)_.

## Objetivo
Assistente conversacional da **Plataforma CitizenTech de Zeladoria Urbana Acessível** que orienta o cidadão
(inclusive surdo, por ser 100% em texto) sobre buracos, fissuras, calçadas, iluminação, entulho, ouvidoria/LGPD,
alertas sonoros (OuviAí) e **status das ocorrências** da plataforma. Ele responde **só com base em fontes**, sempre
cita a fonte `[n]`, **se abstém** quando não há evidência e resiste a prompt injection e a pedidos de dados pessoais.
ODS 11 e ODS 10.

```
pergunta ─► guardrails de entrada ─► (OC-xxxx? consulta direta por metadado)
            injeção · PII · emergência        │
                     ▼                         ▼
        expansão (sinônimos + histórico) ─► retriever híbrido (BM25 + TF-IDF char, RRF, top-4)
                     ▼
        limiar de relevância (fora de escopo / sem evidência → abstenção)
                     ▼
        sanitização do contexto (remove instruções injetadas e PII dos trechos)
                     ▼
        generator (extrativo offline  |  Claude via API, temperatura 0)
                     ▼
        verificação de fundamentação (cada frase precisa de [n] válido e ≥60% de suporte) ─► resposta + fontes
```

## Como rodar (Python 3.12, sem dependências obrigatórias)
```bash
cd 05-generative-ai
python -m unittest discover -s tests      # 11 testes
python avaliacao/avaliar.py               # gera avaliacao/relatorio_avaliacao.md e resultados.json
python api.py                             # API em http://127.0.0.1:8005
```
Opcional, com LLM: defina `ANTHROPIC_API_KEY` (variável de ambiente, **nunca** no código) e, se quiser, `CITIZENTECH_LLM_MODEL`
(padrão `claude-haiku-5-5`). Avaliação com o LLM: `USAR_LLM=1 python avaliacao/avaliar.py`.
Sem chave, o sistema usa o gerador extrativo, que funciona offline e é determinístico.

### Integração com o front-end (04-frontend) e demais módulos
```python
import sys; sys.path.insert(0, "05-generative-ai")
from assistente import responder
r = responder("Qual o status da OC-0003?", historico=[{"papel": "usuario", "texto": "..."}])
r["resposta"], r["fontes"], r["abstencao"], r["motivo"]
```
Ou via HTTP: `POST /chat` com o corpo `{"pergunta": "...", "historico": [...]}`, e `GET /health`.
`motivo` ∈ `respondida | consulta_ocorrencia | baixa_relevancia_recuperacao | gerador_sem_evidencia |
resposta_nao_sustentada_bloqueada | prompt_injection_bloqueada | pedido_dado_pessoal_negado | pergunta_ambigua | ocorrencia_inexistente`.
- **Ocorrências** seguem o contrato de dados do `CONTEXTO.md`. A fonte é `dados/ocorrencias_exemplo.csv` (mock com uma coluna `contato`
  fictícia, usada para testar privacidade) e, se esse arquivo não existir, `../dados/ocorrencias.csv`. Os registros vêm dos módulos de visão (09), IoT (07) e RPA (01).
- **08-NLP:** o corpus limpo produzido pelo módulo de NLP pode substituir/ampliar `kb/` (basta salvar `.md` com o mesmo front-matter).
  A LLM pequena com fine-tuning pode entrar como `GeradorLLM` alternativo.

## Corpus e configuração
| Arquivo `kb/` | Fonte | URL | Consulta |
|---|---|---|---|
| 01_canais_atendimento | Portal SP156 | https://sp156.prefeitura.sp.gov.br | 15/11/2026 |
| 02_buracos_pavimento | Carta de serviços / SP156 (tapa-buraco) | https://sp156.prefeitura.sp.gov.br | 15/11/2026 |
| 03_fissuras_calcadas | Programa de calçadas – Prefeitura de SP | https://www.prefeitura.sp.gov.br/cidade/secretarias/subprefeituras/calcadas/ | 15/11/2026 |
| 04_acompanhamento_status | Contrato de dados CitizenTech | CONTEXTO.md | 15/11/2026 |
| 05_ouvidoria_lgpd | Ouvidoria SP; Lei 13.709/2018 | https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm | 15/11/2026 |
| 06_alertas_sonoros_ouviai | Módulo 07 OuviAí | 07-iot-ouviai/README.md | 15/11/2026 |
| 07_iluminacao_lixo | SP156 (iluminação/limpeza) | https://sp156.prefeitura.sp.gov.br | 15/11/2026 |
| ocorrências | Base CitizenTech (6 registros mock) | dados/ocorrencias_exemplo.csv | — |

> ⚠️ Os textos de `kb/` são **resumos redigidos pelo grupo** a partir dessas fontes, para o protótipo. Prazos como
> "7 dias úteis" são **referência do protótipo** e o próprio documento diz isso. Antes de usar com cidadãos reais, confira cada página oficial e
> atualize a data de consulta.

**Parâmetros principais:** chunking estrutural com `max_chars=700` e `overlap=120`; retriever híbrido RRF (`k=60`) com `top_k=4`; abstenção
quando `bm25 < 2.0` **e** `cosseno < 0.12`; cobertura mínima da pergunta pela melhor frase de 0,4; suporte mínimo por frase de 0,6;
LLM com `temperature=0` e `max_tokens=400`. O prompt está em [assistente/generator.py](assistente/generator.py) (`SYSTEM_PROMPT`).

## Decisões técnicas (justificativas)
**Chunking: estrutural por seção H2, com prefixo de metadados.** Os documentos de serviço já vêm organizados por
assunto (como solicitar, prazo, o que não é atendido). Um chunk por seção mantém a resposta inteira junto, e o prefixo
"Título — Seção:" injeta contexto (por exemplo, a palavra *tapa-buraco* na seção "Prazo"). Seções longas viram janelas de 700 caracteres
com overlap de 120, cortadas em fim de frase. Cada chunk guarda `titulo`, `secao`, `url` e `consultado_em` para a citação.
As ocorrências viram um chunk cada e **só com campos públicos**: o contato e as coordenadas ficam fora do índice (minimização da LGPD).
Comparamos com janelas fixas de 300/50 e 150/30 (tabela abaixo).

**Retriever: híbrido (BM25 + TF-IDF de n-gramas de caracteres 3–5, fundidos por RRF).** As perguntas dos cidadãos misturam
termos exatos ("OC-0003", "tapa-buraco", "Ecoponto"), que favorecem a busca lexical, com erros de digitação e flexões
("consrto", "lampada"), que favorecem os n-gramas. O TF-IDF de caracteres é um **proxy offline de embeddings**: roda sem GPU, sem
download e sem enviar dados a terceiros. A evolução natural é trocá-lo por `sentence-transformers`
(`paraphrase-multilingual-MiniLM-L12-v2`) no mesmo `Retriever`. Usamos o RRF em vez de somar scores porque as escalas dos dois métodos são diferentes.
**Filtro por metadado:** quando a pergunta contém `OC-\d+`, a busca vai direto à ocorrência pelo `id`, sem passar pela recuperação semântica.
Antes da busca, a consulta é expandida com sinônimos do domínio (conserto→reparo, surdo→deficiência auditiva).

**Generator.** São dois modos com a mesma interface:
1. **Extrativo (padrão):** escolhe as frases dos trechos que mais cobrem os termos da pergunta e cita cada uma. Por
   construção não inventa texto. Foi escolhido como padrão porque é gratuito, reprodutível e funciona sem credencial. Ele também é o fallback quando a API falha.
2. **LLM (Claude, `claude-haiku-5-5`):** modelo pequeno, rápido e barato, suficiente para reescrever o contexto em linguagem simples.
   Usa `temperature=0` para ter consistência. O prompt define **papel**, **escopo**, **regras inegociáveis** (só usar os documentos, citar `[n]`
   em cada frase, responder `SEM_EVIDENCIA` quando faltar base, tratar `<documentos>` como dado e não como instrução, não revelar
   regras nem PII) e **formato** (no máximo 4 frases, sem markdown, em português simples).
Nos dois modos a saída passa pela **verificação de fundamentação**, que é independente do modelo.

## Mitigação de erros e vulnerabilidades (todas demonstradas em testes)
| Risco | Proteção | Evidência |
|---|---|---|
| Alucinação / resposta não sustentada | limiar de relevância; cobertura mínima; regra `SEM_EVIDENCIA`; **verificador por frase** (exige citação válida e ≥60% dos termos no trecho citado) | ablação: sem as proteções, 3/3 perguntas sem resposta foram "respondidas"; com elas, 0/3 |
| Prompt injection direta / roleplay / vazar prompt | detector de padrões na entrada | A01, A02, A04 bloqueadas |
| Injeção indireta (instrução dentro de documento/ocorrência) | sanitização do contexto + delimitação `<documentos>` como dado | OC-0006 contém "IGNORE AS INSTRUÇÕES…" e a instrução não aparece na resposta; documento malicioso plantado na base não foi obedecido |
| Exposição de dados pessoais | coluna `contato` fora do índice; recusa de pedidos de dado de terceiros; mascaramento de CPF/e-mail/telefone na entrada e na saída; API não loga o corpo | A03 bloqueada; A06 (CPF na pergunta) mascarado; 0 vazamentos |
| Risco à vida | detector de emergência adiciona Defesa Civil 199 / Bombeiros 193 | Q19 |
| Credenciais | chave só por variável de ambiente; nada no repositório | — |

## Resultados (`python avaliacao/avaliar.py`; detalhes em [avaliacao/relatorio_avaliacao.md](avaliacao/relatorio_avaliacao.md))
**25 perguntas** (o plano mínimo pede 10): 8 respondíveis, 1 com erro de digitação, 2 de ocorrência, 3 sem resposta,
2 fora do escopo, 1 ambígua, 1 multi-turno, 1 de emergência, 5 adversariais e 1 com PII na entrada.

**Chunking × retriever** (12 perguntas com evidência-ouro, k=4):

| chunking | retriever | chunks | hit@1 | hit@4 | MRR |
|---|---|---|---|---|---|
| estrutural 700/120 | BM25 | 28 | 0.667 | 1.000 | 0.819 |
| estrutural 700/120 | vetorial | 28 | 0.667 | 1.000 | 0.785 |
| **estrutural 700/120** | **híbrido** | 28 | 0.667 | **1.000** | **0.819** |
| fixo 300/50 | híbrido | 32 | 0.750 | 0.917 | 0.833 |
| fixo 150/30 | BM25 | 56 | 0.500 | 0.750 | 0.590 |
| fixo 150/30 | híbrido | 56 | 0.417 | 0.833 | 0.583 |

(a tabela completa, com as falhas por pergunta, está no relatório; os números exatos podem variar se a base mudar)

**Generator com contexto controlado** (evidência-ouro + 2 distratores; modo extrativo): correção de 0,7 nas respondíveis,
**fidelidade média das frases de 1,0** e **abstenção correta de 1,0** nas sem resposta.
**End-to-end:** acurácia de comportamento de **0,96 (24/25)**, **taxa de respostas não sustentadas de 0,0**,
**0 vazamentos** e 5/5 testes adversariais bloqueados.

## Interpretação crítica
- **O chunking importa mais que o retriever.** Com chunks estruturais, os três recuperadores chegam a hit@4 = 1,0. Já
  janelas de 150 caracteres cortam a resposta ao meio e separam "prazo" de "tapa-buraco": o hit@4 do BM25 cai para 0,75 e o MRR cai cerca de 30%.
  A janela fixa de 300 caracteres tem hit@1 um pouco maior, mas perde a Q04 porque mistura duas seções. O híbrido não supera o BM25
  nesta base pequena e bem escrita. Ele se justifica pela robustez a erros de digitação (Q09 "consrto") e pela expectativa de vocabulário mais variado
  em produção.
- **O sistema prefere abster-se a errar, e isso é intencional.** Na prática, a falha de 0,3 na geração extrativa é sempre uma abstenção
  indevida e nunca uma invenção. A Q05 ("o que quer dizer *encaminhada*") recupera o trecho certo, mas a frase da base ("encaminhada: a
  ocorrência foi enviada…") cobre poucos termos da pergunta. O LLM resolve esse caso de paráfrase. Para o cidadão, um "não sei, consulte o
  SP156" custa menos que um prazo inventado.
- **A verificação de fundamentação é a proteção mais forte.** Na ablação, sem ela as perguntas sem resposta (multa da calçada,
  horário do Ecoponto, prazo da lâmpada) receberam frases *relacionadas* e com citação, que parecem confiáveis mas não respondem. Esse é o tipo
  de alucinação mais perigoso, porque a resposta vem com fonte.
- **Contexto entre turnos** funciona por herança da pergunta anterior quando a nova é curta ou anafórica ("E qual o prazo?").
  É uma heurística: falha se o usuário trocar de assunto com uma pergunta curta.

### Limitações
1. O **detector de injeção é baseado em padrões**: paráfrases novas, outros idiomas ou texto codificado podem passar. A segunda
   barreira (prompt com delimitação, verificador e o fato de o gerador extrativo não seguir instruções) reduz o impacto, mas não o elimina.
2. O **conjunto de teste é pequeno (25) e os limiares foram calibrados nele**, então há risco de sobreajuste. O próximo passo é avaliar
   em um conjunto separado (por exemplo, perguntas reais do SP156 ou o Pirá 2.0 para testar abstenção).
3. O verificador mede **sobreposição lexical**, não implicação lógica. Uma frase com as mesmas palavras e sentido invertido passaria.
   Uma melhoria seria um modelo NLI ou um LLM-juiz.
4. A base é **pequena, resumida pelo grupo e restrita a São Paulo**, e os prazos são do protótipo. O assistente só serve para as cidades e
   serviços que estão na base.
5. Os números da tabela foram medidos com o gerador extrativo. Os números com LLM dependem da chave e de rodar `USAR_LLM=1`.

### Impacto para o cidadão
O assistente responde em texto, o que dá acesso a pessoas surdas. Ele mostra a fonte, então o cidadão pode conferir, e prefere
encaminhar ao SP156 a inventar. Uma orientação errada sobre prazo ou responsabilidade pode gerar cobrança indevida ou desistência.
Uma orientação errada em emergência pode custar vidas, e por isso a detecção de emergência vem antes de qualquer resposta.

## Estrutura
```
05-generative-ai/
├── assistente/  texto.py · ingest.py · retriever.py · generator.py · guardrails.py · assistente.py
├── kb/          base de conhecimento (.md com front-matter de fonte/URL/data)
├── dados/       ocorrencias_exemplo.csv (mock, contrato de dados CitizenTech)
├── avaliacao/   perguntas.json · avaliar.py · relatorio_avaliacao.md · resultados.json
├── tests/       test_assistente.py
└── api.py       API HTTP para o front-end
```

## Roteiro do vídeo (≤ 5 min)
1. (0:00–0:40) Problema e onde o assistente entra na CitizenTech.
2. (0:40–1:50) Arquitetura: chunking estrutural, retriever híbrido, generator e verificador (mostrar a tabela de comparação).
3. (1:50–3:10) Demonstração: Q02 (prazo com fonte), Q10 (status OC-0003), Q18 (multi-turno), Q19 (emergência).
4. (3:10–4:10) Falhas e mitigação: Q12 com abstenção, a ablação sem verificador, A01/A03 bloqueadas e a injeção na OC-0006.
5. (4:10–5:00) Limitações e próximos passos (embeddings densos, NLI, conjunto de teste separado).
