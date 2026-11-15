# 07 – Physical Computing / Cognitive IoT: OuviAí

Assistente sonoro para pessoas com deficiência auditiva: o celular reconhece **campainha**, **batida na porta** e **ambiente** com um modelo **MFE + CNN** treinado no **Edge Impulse** e mostra a classe na tela (*Deployment → Run this model*).

## Arquivos
| Arquivo | Para quê |
|---|---|
| [GUIA_EDGE_IMPULSE.md](GUIA_EDGE_IMPULSE.md) | Passo a passo: coleta (20×5 s por classe, 15 Training / 5 Test), parâmetros MFE e CNN, Model testing, Run this model, lista de prints |
| [ENTREGA_OuviAi.md](ENTREGA_OuviAi.md) | Documento de entrega completo (capa, problema, ODS, arquitetura, tabelas, erros, limitações), com espaços para prints |
| [validacao_ao_vivo.csv](validacao_ao_vivo.csv) | Planilha das 15 tentativas ao vivo (abre no Excel) |
| [teste_arquivos.csv](teste_arquivos.csv) | Planilha dos 15 WAVs de Test |
| [calcular_acerto.py](calcular_acerto.py) | Calcula % de acerto, matriz de confusão e falsos positivos; opcionalmente gera ocorrências JSON |
| [integracao/](integracao/) | Exemplo de `Ocorrência` no contrato de dados da plataforma |
| `evidencias/` | Prints e vídeo (nomes sugeridos no guia) |

## O que só o aluno faz
1. Gravar os 60 áudios no celular, treinar e testar no Edge Impulse (siga o guia).
2. Rodar o modelo no celular e preencher `classe_prevista` nas duas planilhas.
3. `python calcular_acerto.py validacao_ao_vivo.csv` e `python calcular_acerto.py teste_arquivos.csv` → copiar os números para `ENTREGA_OuviAi.md`.
4. Inserir prints, nomes/RMs, exportar para PDF e entregar no Portal do Aluno (prazo 19/11/2026 23h55).

## Integração com a Plataforma CitizenTech
- **Papel:** módulo de **acessibilidade**: o cidadão surdo recebe alertas visuais dos sons da casa. É o único módulo que roda 100 % no dispositivo (edge AI), sem enviar áudio.
- **Contrato de dados:** quando o usuário opta por registrar, cada detecção vira uma `Ocorrência` com `tipo = "alerta_sonoro"`, `origem = "iot"` e `confianca` = probabilidade da classe (ver [integracao/exemplo_ocorrencia.json](integracao/exemplo_ocorrencia.json)). `python calcular_acerto.py validacao_ao_vivo.csv --ocorrencias` gera `integracao/ocorrencias_iot.json` a partir das tentativas reais.
- **Front End (04):** o painel pode ler esse JSON e mostrar os alertas sonoros junto das ocorrências de visão/chat, com filtro `origem = iot`.
- **RPA (01):** ignora `alerta_sonoro` de prioridade baixa (são pessoais); só sons urbanos de uma versão futura seriam encaminhados à prefeitura.
- **Governança (06):** privacidade por design (inferência local, sem conversas gravadas, consentimento); KPIs = % de acerto ao vivo e taxa de falsos positivos; aviso de que não substitui sistemas de emergência.
- **Cluster (02):** custo de nuvem ≈ zero para este módulo, pois a inferência é distribuída nos celulares.
