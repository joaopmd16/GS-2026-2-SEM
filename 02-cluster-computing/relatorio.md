# Relatório: Cluster Computing na Plataforma CitizenTech de Zeladoria Urbana Acessível

**Disciplina:** Cluster Computing, Computação Neuromórfica e Supercomputadores. GS 2026.2, FIAP 2TIAP.
**Projeto:** CitizenTech: Plataforma de Zeladoria Urbana Acessível
**Integrantes:** ⟨Nome – RM⟩ · ⟨Nome – RM⟩ · ⟨Nome – RM⟩
**Ferramenta:** iSPD ⟨versão⟩

---

## 1. Vínculo com o desafio
A plataforma recebe do cidadão **fotos** de problemas urbanos (a visão computacional detecta fissuras e buracos), **áudios** curtos (o módulo OuviAí classifica sons e gera alertas visuais para pessoas surdas) e **mensagens** ao assistente conversacional (LLM pequena com RAG). Cada inferência gera uma *Ocorrência* (contrato de dados do projeto) com tipo, confiança e prioridade.

Numa cidade, isso significa muitas tarefas independentes e repetidas: cada foto, áudio ou pergunta é uma unidade de trabalho que não depende das outras. Esse padrão (*bag-of-tasks*) é o caso típico em que um **cluster mestre–workers** ajuda: o mestre recebe as requisições e distribui as inferências entre os workers.

**Pergunta norteadora:** o processamento distribuído atende a essa demanda e melhora o tempo de resposta da solução?

## 2. Modelagem da carga (valores estimados e declarados)
Tarefa simulada: **uma inferência de IA da plataforma**, com a mistura de horário de pico abaixo. Lote de **1000 tarefas** (≈ 1 hora de pico numa cidade média: ~600 fotos, ~300 áudios e ~100 conversas).

| Tipo de tarefa | Participação | Custo estimado por tarefa | Dados enviados por tarefa | Base da estimativa |
|---|---|---|---|---|
| Visão (detecção de dano, imagem 640×640) | 60% | ≈ 9 GFLOP | foto ≈ 2 MB ≈ 16 Mbit | detector leve tipo YOLO-nano, ~8–9 GFLOPs por imagem |
| Áudio (classificação de som, 1 s) | 30% | ≈ 0,5 GFLOP | ≈ 0,25 MB ≈ 2 Mbit | CNN pequena sobre espectrograma |
| LLM (resposta de ~300 tokens, modelo de ~1 B parâmetros) | 10% | ≈ 600 GFLOP | texto ≈ 0,1 Mbit | ≈ 2 FLOPs × parâmetros × tokens |
| **Média ponderada** | 100% | **≈ 65 GFLOP = 65 000 MFlop** | **≈ 10 Mbit** | 0,6·9 + 0,3·0,5 + 0,1·600 ≈ 65 |

O iSPD gera um único perfil de tarefa, então usamos a **média ponderada**, com faixa de 10 000 a 120 000 MFlop para representar a variação entre os tipos. A LLM domina o custo (≈ 92% dos FLOPs) mesmo sendo só 10% das tarefas. Esse ponto é discutido na seção 5.

## 3. Parâmetros dos cenários (condições controladas)
| Parâmetro | Cenário A | Cenário B | Unidade |
|---|---|---|---|
| Quantidade de tarefas | 1000 | 1000 | tarefas |
| Tamanho computacional (mín / méd / máx) | 10 000 / 65 000 / 120 000 | igual | MFlop |
| Comunicação por tarefa (mín / méd / máx) | 0,1 / 10 / 20 | igual | Mbit |
| Chegada das tarefas | 0 (lote) | igual | s |
| **Número de workers** | **2** | **4** | máquinas |
| Capacidade de cada worker | 50 000 (1 núcleo) | igual | MFlop/s |
| Mestre | 1, só escalona | igual | n/a |
| Largura de banda (todos os links) | 1000 | igual | Mb/s |
| Latência (todos os links) | 0,001 | igual | s |
| Escalonador | Workqueue | igual | n/a |
| Topologia | Mestre – Switch – Workers | igual | n/a |

Só o número de workers muda. Carga, capacidade, banda, latência e escalonador ficam iguais. Os arquivos estão em `ispd/cenario_A_2workers.imsx` e `ispd/cenario_B_4workers.imsx`. O passo a passo para reconstruir os cenários está em `PASSO_A_PASSO_iSPD.md`.

## 4. Resultados (iSPD)
### 4.1 Tempo total
| Indicador | Cenário A (2 workers) | Cenário B (4 workers) | Unidade |
|---|---|---|---|
| Total Simulated Time | T₂ = ⟨preencher⟩ | T₄ = ⟨preencher⟩ | s |
| Redução percentual (T₂ − T₄)/T₂ | n/a | ⟨preencher⟩ | % |
| Razão T₂/T₄ (speedup) | n/a | ⟨preencher⟩ (ideal = 2,00) | n/a |
| Eficiência (T₂/T₄)/2 | n/a | ⟨preencher⟩ | % |

### 4.2 Distribuição por recurso (aba Resources)
| Worker | A: tarefas | A: MFlop processado | B: tarefas | B: MFlop processado |
|---|---|---|---|---|
| Worker1 | ⟨ ⟩ | ⟨ ⟩ | ⟨ ⟩ | ⟨ ⟩ |
| Worker2 | ⟨ ⟩ | ⟨ ⟩ | ⟨ ⟩ | ⟨ ⟩ |
| Worker3 | n/a | n/a | ⟨ ⟩ | ⟨ ⟩ |
| Worker4 | n/a | n/a | ⟨ ⟩ | ⟨ ⟩ |
| Desbalanceamento (máx/média) | | ⟨ ⟩ | | ⟨ ⟩ |

### 4.3 Evidências
| Cenário A | Cenário B |
|---|---|
| ![modelo A](evidencias/A_modelo.png) | ![modelo B](evidencias/B_modelo.png) |
| ![global A](evidencias/A_global.png) | ![global B](evidencias/B_global.png) |
| ![resources A](evidencias/A_resources.png) | ![resources B](evidencias/B_resources.png) |

*Referência teórica (não é resultado do iSPD, serve só para conferência):* com a mesma carga, `python scripts/analise.py estimar` prevê ≈ 669 s com 2 workers e ≈ 336 s com 4, ou seja, redução ≈ 50% e T₂/T₄ ≈ 2,0.

## 5. Discussão
**Tempo e escalabilidade.** ⟨Interpretar: a redução observada foi de X% e T₂/T₄ = Y. Se Y ≈ 2, a escalabilidade foi praticamente linear. Se Y < 2, apontar a causa: comunicação, desbalanceamento ou tarefas grandes no fim do lote.⟩
Um ganho próximo do linear era esperado porque a carga é dominada por computação. Cada tarefa leva em média 65 000 / 50 000 ≈ **1,3 s** de processamento contra 10 / 1000 + 0,001 ≈ **0,011 s** de transferência, uma razão computação/comunicação de ≈ 120:1. Além disso, as tarefas são independentes.

**Distribuição.** O Workqueue entrega uma nova tarefa a cada worker que fica livre. Isso tende a equilibrar o MFlop processado mesmo com tarefas de tamanhos diferentes. ⟨Comentar a tabela 4.2: os workers ficaram com cargas parecidas? Houve worker ocioso no fim do lote?⟩

**Benefícios para a CitizenTech.** Dobrar os workers reduz o tempo para esvaziar a fila de pico. Na prática, as ocorrências de prioridade alta (buraco em via, alerta sonoro para pessoa surda) chegam mais rápido à prefeitura e ao cidadão. O modelo também mostra que a solução escala horizontalmente: basta adicionar nós quando a demanda da cidade cresce.

**Gargalos e limitações.**
- **Mestre e rede como ponto único.** Todo envio passa pelo link do mestre. Com mais workers, ou com banda baixa (ver o cenário opcional de 10 Mb/s), a comunicação deixa de ser desprezível e o ganho diminui (Lei de Amdahl).
- **Carga média única.** O iSPD usa um perfil médio. Na realidade, as tarefas de LLM (≈ 600 GFLOP) são ~70× mais caras que as de visão e podem se concentrar num worker no fim do lote, aumentando o tempo total.
- **Chegada em lote.** Supusemos as 1000 tarefas no instante 0. Na plataforma real a chegada é contínua (Poisson), e a métrica relevante seria a latência por requisição, não só o tempo total do lote (*makespan*).
- **Hardware abstrato.** Capacidade em MFlop/s não representa memória de GPU, *batching*, carregamento do modelo nem *cold start*. Os FLOPs foram estimados, não medidos na aplicação.
- **Sem falhas nem custo.** O modelo não considera falhas de nós, energia nem custo de nuvem. Mais workers também significam mais custo e mais consumo.

**Extrapolação para o protótipo real.** Os números indicam tendência, não desempenho real. Para validar, seria preciso medir o tempo de inferência dos módulos de visão (pasta `09`), áudio (`07`) e LLM (`05`) numa máquina de referência e recalibrar os parâmetros da carga.

**Computação neuromórfica e supercomputadores (contexto).** A classificação de som do OuviAí é contínua e roda na borda, o que faz dela uma boa candidata a chips neuromórficos (processamento por eventos/*spikes*, consumo muito baixo). Um supercomputador só se justificaria para *treinar* os modelos (por exemplo, o fine-tuning da LLM), não para a inferência do dia a dia, que cabe num cluster pequeno.

## 6. Conclusão
⟨Resumir em 2–3 frases com os números finais. Exemplo: "Com a mesma carga de 1000 inferências, passar de 2 para 4 workers reduziu o tempo de T₂ s para T₄ s (−X%; T₂/T₄ = Y). A carga é limitada por computação e o Workqueue distribuiu bem as tarefas, então o cluster atende ao pico da plataforma. O ganho depende de a comunicação continuar pequena em relação à computação."⟩

## 7. Reprodução
- Parâmetros: `parametros.csv`
- Modelos iSPD: `ispd/*.imsx`
- Passo a passo: `PASSO_A_PASSO_iSPD.md`
- Resultados brutos: `resultados.csv` e `python scripts/analise.py comparar`
