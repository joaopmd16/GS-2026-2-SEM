# 01 · AI for Robotic Process Automation — Robô de Encaminhamento de Chamados

Parte da **Plataforma CitizenTech de Zeladoria Urbana Acessível** (GS 2026.2 · FIAP · 2TIAP).

## Integrantes
> ⚠️ **PREENCHER (aluno):** nome completo e RM de cada integrante (até 5).

| Nome | RM |
|---|---|
| _preencher_ | _preencher_ |

## Problema e público
Ocorrências urbanas (buracos, fissuras, alertas sonoros) chegam por vários canais — foto
analisada pela Visão Computacional (09), sensor sonoro IoT/OuviAí (07), chat do assistente (05).
Hoje alguém precisaria ler cada uma, decidir o tipo e a urgência, descobrir o órgão responsável,
calcular o prazo e mandar e-mail. Isso atrasa o atendimento, principalmente de quem mais depende
de calçadas e vias seguras: **pessoas com deficiência, idosos e crianças**, e pessoas surdas que
dependem de alertas visuais.

O robô automatiza essa tarefa **de ponta a ponta**: lê os chamados, valida, classifica com IA,
descobre o destino por scraping, calcula o prazo em dias úteis via API, grava em SQL e envia
o e-mail ao órgão, com os dados pessoais mascarados. O que ele não consegue decidir com
segurança vai para **revisão humana**.

## Fluxo

```
CSV de ocorrências ──► [Pandas] validação ──► quarentena.csv (inválidas, com motivo)
        │
        ▼
 [IA] tipo + prioridade + confiança ──► confiança < 0,5 ──► revisao_humana.csv
        │
        ▼
 [Scraping] página da prefeitura ──► órgão, e-mail e prazo por tipo  (falhou → tabela padrão)
        │
        ▼
 [API BrasilAPI] feriados ──► prazo em dias úteis                    (falhou → sem feriados)
        │
        ▼
 [SQL/SQLite] já foi enviado? ──► sim: não reenvia (idempotência)
        │ não
        ▼
 [E-mail] .eml (ou SMTP) com CPF/telefone/e-mail mascarados ──► registro em `envios`
        │
        ▼
 relatorio_execucao.json + tabela `execucoes` + robo.log
```

## Quadro de temas (5 temas da disciplina, cada um com função real)

| Tema | Onde está no fluxo | O que resolve | Por que escolhemos |
|---|---|---|---|
| **Pandas** | `robo/ingestao.py` | Lê o CSV do contrato de dados, normaliza tipos, valida 7 regras (id, duplicado, descrição, coordenada, data, origem, confiança) e separa a quarentena | Os outros módulos (visão, IoT, chat) gravam no mesmo CSV; precisamos limpar antes de agir |
| **Web scraping** (requests + BeautifulSoup) | `robo/scraping.py` | Lê a tabela “órgão responsável / e-mail / prazo” da página de serviços da prefeitura | O destino muda quando a prefeitura atualiza o site; o robô sempre lê a versão atual em vez de ter isso fixo no código |
| **APIs REST** | `robo/api.py` (BrasilAPI `/feriados`) | Calcula o prazo do chamado em dias úteis, sem contar feriados | Prazo honesto para o cidadão; API pública, gratuita e sem chave. Só o **ano** é enviado |
| **SQL (SQLite)** | `robo/banco.py` | Persiste ocorrências, controla envios (idempotência) e guarda o histórico de execuções; consultas de resumo por bairro e prioridade | Rodar o robô de novo não pode mandar o mesmo e-mail duas vezes |
| **E-mail automático** | `robo/email_bot.py` | Monta e envia o chamado ao órgão (modo `arquivo` gera `.eml`; modo `smtp` envia de verdade) | É o canal que a prefeitura já usa; não exige integração com sistema interno |
| **IA (NLP por regras + modelo da disciplina 09)** | `robo/ia.py` | Classifica tipo e prioridade pelo texto; usa o tipo do modelo de Visão quando ele tem confiança ≥ 0,6; baixa confiança → revisão humana | Sem custo e explicável; o enunciado permite regras/NLP e modelos de outras disciplinas. LLM não foi usado |

## Como executar

Requisitos: Python 3.12.

```bash
cd 01-rpa-ia
pip install -r requirements.txt
python main.py --limpar        # execução completa com os dados de teste
python avaliar.py              # mede a IA no conjunto rotulado -> evidencias/avaliacao.md
python -m pytest -q tests      # 11 testes (casos normais e de falha)
```

Outras formas:
- `python main.py --entrada ../dados/ocorrencias.csv` processa a base compartilhada do projeto.
- `python main.py` de novo **não reenvia** nada (idempotência). `--limpar` apaga `saida/` e recomeça.
- Sem internet: `ROBO_OFFLINE=1` (o prazo é calculado sem feriados, e o log avisa).

Saídas em `saida/` (não versionada): `robo.log`, `relatorio_execucao.json`, `quarentena.csv`,
`revisao_humana.csv`, `outbox/*.eml`, `citizentech_rpa.db`.

### Configurar chaves e senhas
Nenhuma chave é obrigatória: o modo padrão grava os e-mails como arquivo e a BrasilAPI não usa chave.
Para enviar e-mail de verdade, copie `.env.example` para `.env` e preencha `EMAIL_MODO=smtp`,
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` e `SMTP_PASS`. Por exemplo, Gmail com *senha de app*.
O `.env` está no `.gitignore` e **nunca** vai para o repositório. As credenciais são lidas só de
variáveis de ambiente.

## Resiliência e segurança

| Falha previsível | Tratamento |
|---|---|
| Arquivo de entrada ausente ou ilegível | log ERROR, DataFrame vazio, robô termina normalmente com relatório |
| Dado inválido (id, coordenada, data, origem, duplicado...) | vai para `quarentena.csv` com o motivo, e o resto segue |
| Site fora do ar ou layout mudou | `timeout=5s` + **retry com espera exponencial** (3×), depois tabela padrão |
| API de feriados com erro, resposta inválida ou offline | timeout + retry; **cache local**; depois prazo sem feriados |
| Falha de SMTP | retry; o e-mail fica salvo em `outbox/falhas/` para reenvio; a falha é contada no relatório |
| Erro inesperado num registro | `rollback` só daquele registro; os outros continuam (`falhas` no relatório) |
| IA incerta (confiança < 0,5) | não envia: vai para **revisão humana** |
| Reexecução | **idempotência** via tabela `envios` (chave primária = id da ocorrência) |

## Evidências de validação (pasta `evidencias/`)

- `execucao_1.txt`: execução completa com 31 registros de teste: **25 válidos, 6 em quarentena,
  20 encaminhados, 5 para revisão humana, 0 falhas**.
- `execucao_2_idempotente.txt`: segunda execução, **0 reenviados, 20 reconhecidos como já enviados**.
- `falha_tratada.txt`: **caso de falha demonstrado**: arquivo de entrada inexistente e portal fora do ar
  (3 tentativas com espera de 0,5 s e 1 s, depois tabela padrão). O robô termina sem travar.
- `quarentena.csv`: os 6 registros inválidos e o motivo de cada um.
- `revisao_humana.csv`: os 5 casos que o robô não decidiu sozinho.
- `exemplo_email_OC-1012.eml`: e-mail gerado. O CPF do cidadão aparece como `[CPF]`.
- `relatorio_execucao.json`: relatório da execução, com resumo por bairro e prioridade (consulta SQL).
- `testes_pytest.txt`: **11/11 testes passando**.
- `avaliacao.md`: resultado medido no conjunto rotulado.

### Resultado medido da IA (amostra de 25 ocorrências sintéticas rotuladas à mão)

| Métrica | Resultado |
|---|---|
| Acurácia do **tipo** | **96 %** (24/25) |
| Acurácia da **prioridade** | **76 %** (19/25) |
| Enviadas para revisão humana | 5/25 (20 %) |

**Análise dos erros e limites:**
- O único erro de tipo foi “vazamento… faz um **som** de chiado”. A palavra “som” levou o texto para
  `alerta_sonoro`, mas era `outro`. Regras por palavra-chave não entendem contexto.
- A prioridade erra mais, quase sempre para baixo: o robô deu `media` quando o certo era `alta`
  (viaduto, estrondo, alarme com pessoa surda, creche). Faltam palavras como “creche”, “viaduto” e
  “incêndio”. Esses erros de **subpriorização** são os mais graves para o cidadão. Por isso o
  e-mail sempre vai e o prazo é só uma sugestão.
- Tudo o que caiu em `outro` foi para revisão humana. Itens urgentes, como “árvore caiu bloqueando
  a rua”, dependem dessa revisão.
- A amostra é pequena e **sintética**, escrita pelo próprio grupo. Os números não valem para dados
  reais. O próximo passo seria trocar as regras pelo classificador da disciplina de NLP (08) e
  medir com chamados públicos anonimizados.

## Proteção de dados, ética e ODS
O robô trabalha só com **dados sintéticos**. Antes de qualquer saída (e-mail, arquivo de envio),
`robo/privacidade.py` mascara CPF, e-mail, telefone e placa (**LGPD**: minimização e finalidade).
A API externa recebe apenas o ano, e nenhum dado pessoal sai para serviços de terceiros. Credenciais
ficam fora do código, em `.env` ignorado pelo Git. Do ponto de vista ético, o robô **não decide
sozinho quando está incerto**: casos de baixa confiança vão para um servidor humano. Cada decisão
fica registrada em log e no banco (rastreabilidade). Sabemos que a regra de prioridade pode
**subestimar** riscos e mostramos isso nos números acima. A prioridade de casos com pessoas com
deficiência, idosos e crianças existe para reduzir desigualdades no atendimento. Assim o protótipo
contribui para o **ODS 11** (cidades sustentáveis: zeladoria mais rápida), o **ODS 10**
(acessibilidade e prioridade a grupos vulneráveis) e o **ODS 9** (manutenção da infraestrutura).

## Integração com os outros módulos
- **Entrada:** `dados/ocorrencias.csv`, no contrato do `CONTEXTO.md`, preenchido pela Visão (09,
  `origem=visao` com `confianca`), pelo IoT/OuviAí (07, `origem=iot`) e pelo chat (05, `origem=chat`).
- **Saída:** status `encaminhada` e prioridade no SQLite (`saida/citizentech_rpa.db`, tabela
  `ocorrencias`, mesmas colunas do contrato), para o painel do Front End (04) ler.
- O volume de chamados processados pode alimentar a simulação do Cluster (02) e a fila de inspeções
  da Quântica (03).

## Estrutura
```
01-rpa-ia/
├── main.py               # ponto de entrada
├── avaliar.py            # avaliação da IA
├── robo/                 # util, ingestao, ia, scraping, api, banco, email_bot, privacidade, pipeline
├── dados_teste/          # 31 ocorrências sintéticas, rótulos e página simulada da prefeitura
├── tests/test_robo.py    # pytest
├── evidencias/           # saídas reais das execuções
├── .env.example  requirements.txt  .gitignore
```

## O que falta o aluno fazer
1. **Preencher integrantes (nome e RM)** na tabela acima.
2. Conferir e ajustar o texto de problema, ética e ODS ao discurso do grupo e ao vídeo da Governança (06).
3. *(Opcional, valoriza)* Testar o modo `EMAIL_MODO=smtp` com uma conta própria e senha de app, e
   anexar um print do e-mail recebido em `evidencias/`. **Não commitar o `.env`.**
4. *(Opcional)* Gravar um trecho de tela rodando `python main.py --limpar` para o vídeo integrador.
5. A página `dados_teste/portal_prefeitura.html` é **simulada**. Se o grupo quiser, aponte
   `PORTAL_URL` para uma página pública real com uma tabela no mesmo formato e mencione isso na entrega.
6. Entregar até **19/11/2026 às 23h55** no Portal do Aluno, com o link do repositório.
