# Avaliação da IA (classificador de tipo e prioridade)

Amostra: **25 ocorrências sintéticas rotuladas manualmente** (`dados_teste/rotulos.csv`).

| Métrica | Resultado |
|---|---|
| Acurácia tipo (todas) | 96% (24/25) |
| Acurácia prioridade (todas) | 76% (19/25) |
| Enviadas p/ revisão humana | 5/25 |
| Acurácia tipo só nas decididas automaticamente | 95% (20 casos) |

## Matriz de confusão — tipo

| real          |   alerta_sonoro |   buraco |   fissura |   outro |
|:--------------|----------------:|---------:|----------:|--------:|
| alerta_sonoro |               4 |        0 |         0 |       0 |
| buraco        |               0 |       10 |         0 |       0 |
| fissura       |               0 |        0 |         6 |       0 |
| outro         |               1 |        0 |         0 |       4 |

## Matriz de confusão — prioridade

| real   |   alta |   baixa |   media |
|:-------|-------:|--------:|--------:|
| alta   |      7 |       0 |       4 |
| baixa  |      0 |       5 |       1 |
| media  |      0 |       1 |       7 |

## Erros (para análise)

| id      | descricao                                                          | tipo_real     | tipo_ia       | prioridade_real   | prioridade_ia   | revisao_humana   |
|:--------|:-------------------------------------------------------------------|:--------------|:--------------|:------------------|:----------------|:-----------------|
| OC-1004 | Rachadura grande na parede do viaduto perto do terminal            | fissura       | fissura       | alta              | media           | False            |
| OC-1009 | Barulho de estrondo forte vindo do prédio vizinho                  | alerta_sonoro | alerta_sonoro | alta              | media           | False            |
| OC-1015 | Alarme de incêndio tocando no prédio e moradora surda não percebeu | alerta_sonoro | alerta_sonoro | alta              | media           | False            |
| OC-1018 | Fissura fina no pilar da passarela                                 | fissura       | fissura       | media             | baixa           | False            |
| OC-1019 | Vazamento de água na rua faz um som de chiado                      | outro         | alerta_sonoro | media             | media           | False            |
| OC-1021 | Buraco na rua da creche. Contato joao.silva@email.com              | buraco        | buraco        | alta              | media           | False            |
| OC-1022 | Barulho alto de obra de madrugada                                  | alerta_sonoro | alerta_sonoro | baixa             | media           | False            |
