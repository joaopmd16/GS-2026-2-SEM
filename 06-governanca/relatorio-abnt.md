<!--
Relatório no formato ABNT/FIAP (NBR 14724).
Ao converter para DOCX: papel A4; margens sup./esq. 3 cm e inf./dir. 2 cm;
Arial ou Times 12; espaçamento 1,5; citações longas, notas e legendas em 10;
títulos de seção numerados; numeração de página a partir da Introdução (canto superior direito).
Marcadores [PENDENTE ...] indicam conteúdo que depende dos resultados dos outros módulos.
Meta: 10 a 15 páginas.
-->

<div align="center">

FIAP – FACULDADE DE INFORMÁTICA E ADMINISTRAÇÃO PAULISTA
CURSO SUPERIOR DE TECNOLOGIA EM INTELIGÊNCIA ARTIFICIAL – TURMA 2TIAP

<br><br><br>

**[NOME COMPLETO DO INTEGRANTE] – RM [00000]**

<br><br><br><br>

**PLATAFORMA CITIZENTECH DE ZELADORIA URBANA ACESSÍVEL**

Relatório integrador da Global Solution 2026.2

<br><br><br><br><br>

SÃO PAULO
2026

</div>

<div style="page-break-after: always;"></div>

<div align="center">

**[NOME COMPLETO DO INTEGRANTE] – RM [00000]**

<br><br><br>

**PLATAFORMA CITIZENTECH DE ZELADORIA URBANA ACESSÍVEL**

</div>

<div align="right" style="margin-left:50%">

Relatório apresentado à disciplina de Governança em IA e Business Analytics do Curso Superior de Tecnologia em Inteligência Artificial da FIAP, como requisito de avaliação da Global Solution 2026.2.

Professor(a): [NOME DO PROFESSOR]

</div>

<div align="center">

<br><br><br>

SÃO PAULO
2026

</div>

<div style="page-break-after: always;"></div>

## LISTA DE QUADROS

Quadro 1 – Papel de cada disciplina na plataforma
Quadro 2 – Contrato de dados da entidade Ocorrência
Quadro 3 – Matriz de riscos de IA
Quadro 4 – Tratamento de dados pessoais segundo a LGPD
Quadro 5 – Indicadores de desempenho (KPIs)
Quadro 6 – Matriz de integração dos módulos

## LISTA DE FIGURAS

Figura 1 – Arquitetura integrada da plataforma
Figura 2 – Fluxo de vida de uma ocorrência
[PENDENTE] Figuras 3 a 11 – capturas de tela dos módulos 01 a 09

## LISTA DE ABREVIATURAS E SIGLAS

| Sigla | Significado |
|---|---|
| ANPD | Autoridade Nacional de Proteção de Dados |
| BA | Business Analytics |
| KPI | Key Performance Indicator (indicador-chave de desempenho) |
| LGPD | Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018) |
| LLM | Large Language Model (modelo de linguagem de grande porte) |
| ODS | Objetivos de Desenvolvimento Sustentável |
| PQC | Post-Quantum Cryptography (criptografia pós-quântica) |
| QAOA | Quantum Approximate Optimization Algorithm |
| RAG | Retrieval-Augmented Generation |
| RIPD | Relatório de Impacto à Proteção de Dados Pessoais |
| RPA | Robotic Process Automation |

<div style="page-break-after: always;"></div>

## SUMÁRIO

1 INTRODUÇÃO
2 DESENVOLVIMENTO
2.1 Arquitetura integrada
2.2 RPA com IA
2.3 Cluster Computing
2.4 Computação Quântica
2.5 Front End
2.6 Generative AI
2.7 IoT (OuviAí)
2.8 Processamento de Linguagem Natural
2.9 Visão Computacional
2.10 Governança em IA e Business Analytics
3 CONCLUSÃO
4 LINKS
REFERÊNCIAS

<div style="page-break-after: always;"></div>

## 1 INTRODUÇÃO

A manutenção de calçadas, vias e muros depende, em boa parte, de o cidadão perceber o problema e conseguir avisar a prefeitura. Esse caminho costuma ser lento e pouco acessível: formulários longos, telefones de atendimento e nenhum retorno sobre o andamento do chamado. Pessoas com deficiência auditiva enfrentam uma barreira a mais, pois parte dos canais e dos alertas do dia a dia é sonora.

A Plataforma CitizenTech de Zeladoria Urbana Acessível foi proposta para reduzir esse atrito. O cidadão envia uma foto, conversa com um assistente ou recebe alertas visuais no celular; a plataforma transforma essas entradas em ocorrências padronizadas, define a prioridade e encaminha o chamado ao órgão responsável. O trabalho está ligado ao ODS 11 (cidades e comunidades sustentáveis), ao ODS 10 (redução das desigualdades) e ao ODS 9 (indústria, inovação e infraestrutura).

O projeto reúne as nove disciplinas do semestre. Cada uma constrói um módulo, e todos compartilham o mesmo contrato de dados. Este relatório descreve cada módulo, a forma como se conectam e, na seção de Governança, avalia o que foi integrado, os riscos éticos e legais envolvidos e os indicadores usados para medir o resultado.

## 2 DESENVOLVIMENTO

### 2.1 Arquitetura integrada

Todos os módulos produzem ou consomem a mesma entidade, a Ocorrência. Essa escolha permite que cada disciplina trabalhe de forma independente e, ainda assim, alimente um painel único.

**Quadro 1 – Papel de cada disciplina na plataforma**

| Módulo | Disciplina | Papel |
|---|---|---|
| 01 | RPA com IA | Lê ocorrências, consulta APIs e envia e-mail automático à prefeitura |
| 02 | Cluster Computing | Simula no iSPD a carga de processamento da plataforma |
| 03 | Computação Quântica | Roteiro quântico (QAOA) para fila de inspeções e uso de PQC |
| 04 | Front End | Interface única: foto, chat e painel de ocorrências |
| 05 | Generative AI | Assistente conversacional com RAG |
| 06 | Governança e BA | Ética, LGPD, riscos, KPIs e integração |
| 07 | IoT (OuviAí) | Reconhecimento de sons no celular e alerta visual |
| 08 | NLP | Corpus extraído de documentos da prefeitura para ajuste de LLM |
| 09 | Visão Computacional | Detecção de fissuras e buracos em fotos |

Fonte: elaborado pelo autor (2026).

**Quadro 2 – Contrato de dados da entidade Ocorrência**

| Campo | Tipo | Valores / exemplo |
|---|---|---|
| id | texto | OC-0001 |
| tipo | categoria | fissura, buraco, alerta_sonoro, outro |
| origem | categoria | visao, iot, chat, rpa |
| descricao | texto | "Buraco na via" |
| confianca | número (0 a 1) | 0,91 |
| latitude, longitude | número | -23,55; -46,63 |
| bairro | texto | Sé |
| prioridade | categoria | baixa, media, alta |
| status | categoria | aberta, encaminhada, em_inspecao, resolvida |
| criado_em | data ISO-8601 | 2026-11-10T09:00:00 |

Fonte: CONTEXTO.md do repositório do projeto (2026).

**Figura 1 – Arquitetura integrada da plataforma**

```
   Cidadão (foto, voz/texto, som ambiente)
        |              |                 |
   [09 Visão]     [05 GenAI + 08 NLP]  [07 IoT OuviAí]
        \              |                 /
         +----> Ocorrência (contrato único) <----+
                       |
              dados/ocorrencias.csv / SQLite
                       |
     +-----------------+------------------+
     |                 |                  |
 [01 RPA]       [03 Quântica]       [04 Front End]
 e-mail e APIs  fila de inspeção    painel e chat
     |                                    |
 Prefeitura                     [06 Governança: KPIs, LGPD, riscos]
                       |
          [02 Cluster: dimensionamento da carga]
```

Fonte: elaborado pelo autor (2026).

**Figura 2 – Fluxo de vida de uma ocorrência**

```
aberta --(RPA envia e-mail)--> encaminhada --(fila priorizada)--> em_inspecao --> resolvida
```

Fonte: elaborado pelo autor (2026).

### 2.2 RPA com IA

O módulo de RPA lê as ocorrências abertas com Pandas ou SQL, complementa os dados por scraping ou API (por exemplo, órgão responsável pelo bairro) e envia um e-mail padronizado à prefeitura. Após o envio, o status passa de "aberta" para "encaminhada", o que alimenta diretamente o KPI de taxa de encaminhamento.

[PENDENTE módulo 01: descrever as fontes usadas, o formato do e-mail, quantidade de chamados processados no teste e incluir captura de tela (Figura 3).]

### 2.3 Cluster Computing

A plataforma executa modelos de visão e de linguagem, que exigem mais processamento do que um servidor simples oferece em horários de pico. O módulo simula essa carga no simulador iSPD, comparando configurações de máquinas e tempos de resposta.

[PENDENTE módulo 02: cenários simulados, número de máquinas, tempo médio de resposta e conclusão sobre o dimensionamento (Figura 4).]

### 2.4 Computação Quântica

O gargalo escolhido foi a ordenação da fila de inspeções e das rotas das equipes, um problema combinatório. O módulo propõe um roteiro de adoção de QAOA e discute criptografia pós-quântica para proteger os dados dos cidadãos, em linha com a LGPD.

[PENDENTE módulo 03: resultado da modelagem, comparação com a solução clássica e roteiro em etapas (Figura 5).]

### 2.5 Front End

A interface, em Streamlit ou Gradio, reúne os módulos em uma só tela: envio de foto, conversa com o assistente e painel de ocorrências com filtros por bairro, tipo e status. É também o ponto onde o cidadão vê o aviso de privacidade e o andamento do seu chamado.

[PENDENTE módulo 04: telas implementadas, quais módulos foram conectados de fato e endereço de execução (Figura 6).]

### 2.6 Generative AI

O assistente conversacional usa RAG sobre documentos de serviços da prefeitura para orientar o cidadão e, quando há um problema a relatar, registra a ocorrência com origem "chat". As respostas citam a fonte consultada, o que reduz o risco de informação inventada.

[PENDENTE módulo 05: modelo utilizado, base de documentos, exemplos de perguntas e respostas (Figura 7).]

### 2.7 IoT (OuviAí)

O OuviAí roda no celular e reconhece sons como campainha e batidas por meio de um modelo treinado no Edge Impulse. Ao detectar um som, mostra um alerta visual, atendendo pessoas surdas. O processamento acontece no próprio aparelho, de modo que o áudio não precisa sair do celular. Eventos relevantes podem virar ocorrências do tipo "alerta_sonoro".

[PENDENTE módulo 07: classes treinadas, acurácia obtida no Edge Impulse e demonstração (Figura 8).]

### 2.8 Processamento de Linguagem Natural

A ferramenta recebe documentos da prefeitura, faz a limpeza do texto e gera três corpus (conversacional, perguntas e respostas e texto puro) para o ajuste fino de um modelo de linguagem pequeno, usado pelo assistente do módulo 05.

[PENDENTE módulo 08: documentos processados, tamanho de cada corpus e exemplos (Figura 9).]

### 2.9 Visão Computacional

O modelo de visão analisa a foto enviada pelo cidadão, identifica fissura ou buraco e devolve a classe com um grau de confiança. Esse valor vai para o campo "confianca" da ocorrência e é usado pela Governança como gatilho de revisão humana.

[PENDENTE módulo 09: arquitetura do modelo, base de imagens, métricas (precisão, recall, mAP) e exemplos de detecção (Figura 10).]

### 2.10 Governança em IA e Business Analytics

Esta seção trata da plataforma como um todo: quem responde por cada decisão automatizada, quais dados pessoais circulam, que riscos existem e como medir se a solução está cumprindo seu objetivo.

#### 2.10.1 Princípios e papéis

A governança adotada segue princípios presentes nas diretrizes de IA da OCDE e no Projeto de Lei 2.338/2023: finalidade definida, supervisão humana, transparência, não discriminação e prestação de contas. Na prática, isso se traduz em três regras para a plataforma:

a) nenhuma decisão automatizada fecha um chamado: a mudança para "resolvida" é sempre feita por um servidor;
b) ocorrências com confiança abaixo de 0,6 vão para revisão humana antes do encaminhamento;
c) o cidadão é informado, na interface, de que está interagindo com um sistema de IA.

Os papéis previstos são o controlador (prefeitura), o operador (equipe que mantém a plataforma), o encarregado de dados e um comitê de IA responsável por aprovar novos modelos e revisar os indicadores.

#### 2.10.2 Ética e LGPD

A plataforma trata dados pessoais: localização, imagens que podem conter rostos e placas, mensagens de texto e, no OuviAí, sons do ambiente doméstico. A base legal principal é a execução de políticas públicas pela administração (art. 7º, III e art. 23 da LGPD). Para o uso do áudio e para dados de pessoas com deficiência, que podem revelar informação de saúde, aplica-se o regime de dados sensíveis (art. 11).

**Quadro 4 – Tratamento de dados pessoais segundo a LGPD**

| Dado | Módulo | Finalidade | Medida de proteção |
|---|---|---|---|
| Foto da via | 09 | Detectar o dano | Desfoque de rostos e placas antes de armazenar |
| Geolocalização | 04, 09 | Localizar o problema | Arredondamento a ~100 m no painel público |
| Mensagens do chat | 05 | Orientar e registrar | Não usar em treino sem consentimento; retenção de 90 dias |
| Áudio ambiente | 07 | Alerta visual | Processamento local; o áudio não é enviado |
| E-mail/contato | 01 | Retorno do chamado | Opcional; acesso restrito ao operador |
| Documentos públicos | 08 | Treinar o assistente | Remoção de dados pessoais antes de gerar o corpus |

Fonte: elaborado pelo autor com base na Lei 13.709/2018 (2026).

Recomenda-se elaborar um RIPD antes da operação real, além de manter registro das operações de tratamento (art. 37) e um canal para o titular pedir acesso ou exclusão de seus dados (art. 18). O módulo 03 complementa essas medidas ao avaliar o uso de criptografia pós-quântica para os dados armazenados a longo prazo.

#### 2.10.3 Riscos de IA

**Quadro 3 – Matriz de riscos de IA**

| Risco | Módulo | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| Falso negativo na detecção de buraco | 09 | Média | Alto | Cidadão pode registrar manualmente; limiar revisado mensalmente |
| Viés geográfico: bairros com menos usuários recebem menos atenção | 04, 06 | Alta | Alto | KPI de ocorrências por mil habitantes; inspeção ativa em bairros sub-representados |
| Resposta inventada pelo assistente | 05, 08 | Média | Médio | RAG com citação da fonte; recusa quando não há documento |
| Som não reconhecido pelo OuviAí | 07 | Média | Alto | Aviso claro de que o app não substitui alarmes de segurança |
| E-mail enviado a órgão errado | 01 | Baixa | Médio | Tabela de órgãos revisada; registro de envios |
| Vazamento de dados de localização | Todos | Baixa | Alto | Controle de acesso, criptografia e anonimização |
| Sobrecarga em pico de uso | 02 | Média | Médio | Dimensionamento definido na simulação do cluster |

Fonte: elaborado pelo autor (2026).

O viés geográfico merece destaque. Uma plataforma que depende do celular e da iniciativa do cidadão tende a registrar mais problemas nos bairros com maior renda e conectividade. Se a fila de inspeções seguir apenas o volume de chamados, a desigualdade aumenta, o que contraria o ODS 10. Por isso a priorização considera também a gravidade e a cobertura por região, e não apenas a contagem de chamados.

#### 2.10.4 Indicadores e Business Analytics

Os indicadores abaixo são calculados pelo script `06-governanca/kpis.py` a partir da base compartilhada `dados/ocorrencias.csv`.

**Quadro 5 – Indicadores de desempenho (KPIs)**

| KPI | Fórmula | Meta sugerida | Valor na base de exemplo |
|---|---|---|---|
| Taxa de encaminhamento | ocorrências não abertas / total | ≥ 90% em 24 h | 50,0% |
| Taxa de resolução | resolvidas / total | ≥ 60% em 30 dias | 0,0% |
| Tempo médio até encaminhamento | média (envio − criação) | ≤ 1 h | [PENDENTE módulo 01] |
| Confiança média da visão | média de "confianca" (origem visão) | ≥ 0,80 | 0,845 |
| Casos para revisão humana | confiança < 0,6 | monitorar | 0 |
| Ocorrências alta prioridade | alta / total | monitorar | 50,0% |
| Distribuição por bairro | contagem por bairro | sem bairro descoberto | Sé 1; Consolação 1 |
| Uso por origem | contagem por origem | ≥ 3 canais ativos | visão 2 |
| Precisão do modelo de visão | métrica do módulo 09 | ≥ 0,85 | [PENDENTE módulo 09] |
| Acurácia do OuviAí | métrica do módulo 07 | ≥ 0,85 | [PENDENTE módulo 07] |

Fonte: elaborado pelo autor (2026). Base de exemplo com 2 registros.

[PENDENTE: rodar `python 06-governanca/kpis.py` sobre a base final, depois que os módulos 01, 05, 07 e 09 gravarem suas ocorrências, e atualizar a última coluna. Incluir gráfico do painel do módulo 04.]

#### 2.10.5 Matriz de integração

O enunciado pede que a Governança mostre o que foi e o que não foi integrado. O quadro a seguir deve ser atualizado ao final do projeto.

**Quadro 6 – Matriz de integração dos módulos**

| Módulo | Grava Ocorrência no contrato? | Conectado ao Front End? | Evidência no GitHub | Situação |
|---|---|---|---|---|
| 01 RPA | [PENDENTE] | [PENDENTE] | 01-rpa-ia/ | [PENDENTE] |
| 02 Cluster | Não se aplica (simulação) | Não | 02-cluster-computing/ | [PENDENTE] |
| 03 Quântica | Não se aplica (estudo) | Não | 03-computacao-quantica/ | [PENDENTE] |
| 04 Front End | Lê e grava | Sim | 04-frontend/ | [PENDENTE] |
| 05 GenAI | [PENDENTE] | [PENDENTE] | 05-generative-ai/ | [PENDENTE] |
| 06 Governança | Lê (KPIs) | [PENDENTE] | 06-governanca/ | Integrado |
| 07 IoT | [PENDENTE] | [PENDENTE] | 07-iot-ouviai/ | [PENDENTE] |
| 08 NLP | Não (gera corpus para 05) | [PENDENTE] | 08-nlp/ | [PENDENTE] |
| 09 Visão | [PENDENTE] | [PENDENTE] | 09-visao-computacional/ | [PENDENTE] |

Fonte: elaborado pelo autor (2026).

Módulos de natureza analítica, como Cluster Computing e Computação Quântica, não trocam dados em tempo de execução com a plataforma. Sua integração é de projeto: o primeiro define a infraestrutura necessária e o segundo orienta a evolução da fila de inspeções e da segurança dos dados.

## 3 CONCLUSÃO

<!--
ATENÇÃO: o enunciado proíbe gerar a conclusão com IA (apenas revisão é permitida).
Este tópico deve ser escrito pelo próprio aluno. Sugestão de pontos a cobrir, com suas palavras:
- o objetivo foi atingido? o que funcionou de ponta a ponta na demonstração;
- o que ficou de fora da integração e por quê (ver Quadro 6);
- principal aprendizado sobre governança (ex.: viés geográfico, revisão humana);
- próximos passos.
Tamanho sugerido: 3 a 4 parágrafos.
-->

[A SER REDIGIDO PELO ALUNO]

## 4 LINKS

| Item | Endereço |
|---|---|
| Vídeo (YouTube, não listado) | [PENDENTE] |
| Repositório GitHub | https://github.com/joaopmd16/GS-2026-2-SEM |

## REFERÊNCIAS

BRASIL. **Lei nº 13.709, de 14 de agosto de 2018**. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 15 nov. 2026.

BRASIL. Senado Federal. **Projeto de Lei nº 2.338, de 2023**. Dispõe sobre o uso da inteligência artificial. Brasília, DF: Senado Federal, 2023. Disponível em: https://www25.senado.leg.br/web/atividade/materias/-/materia/157233. Acesso em: 15 nov. 2026.

ORGANIZAÇÃO DAS NAÇÕES UNIDAS. **Transformando nosso mundo**: a Agenda 2030 para o Desenvolvimento Sustentável. Nova York: ONU, 2015.

ORGANISATION FOR ECONOMIC CO-OPERATION AND DEVELOPMENT. **Recommendation of the Council on Artificial Intelligence**. Paris: OECD, 2019. Disponível em: https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0449. Acesso em: 15 nov. 2026.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.
