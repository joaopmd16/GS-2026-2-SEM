# 02 · Cluster Computing, Computação Neuromórfica e Supercomputadores

## Objetivo
Avaliar no simulador **iSPD** se um cluster mestre–workers atende à carga de inferências de IA da Plataforma CitizenTech (visão computacional, áudio do OuviAí e LLM do assistente), comparando **2 e 4 workers** com todas as demais condições iguais.

## Arquivos
| Arquivo | Conteúdo |
|---|---|
| [relatorio.md](relatorio.md) | Relatório de entrega (2–4 páginas), com espaços `⟨preencher⟩` para os resultados |
| [PASSO_A_PASSO_iSPD.md](PASSO_A_PASSO_iSPD.md) | Roteiro exato para montar e rodar os dois cenários |
| [parametros.csv](parametros.csv) | Todos os parâmetros e unidades dos cenários |
| [resultados.csv](resultados.csv) | Planilha a preencher com os números do iSPD |
| [scripts/analise.py](scripts/analise.py) | `estimar`: estimativa teórica de conferência · `comparar`: redução %, T₂/T₄ e eficiência |
| `ispd/` | Onde salvar `cenario_A_2workers.imsx` e `cenario_B_4workers.imsx` |
| `evidencias/` | Capturas de tela do iSPD (modelo, Global, Resources) |

## Como rodar
1. Siga o [PASSO_A_PASSO_iSPD.md](PASSO_A_PASSO_iSPD.md) no iSPD (Java).
2. Preencha `resultados.csv` e rode `python scripts/analise.py comparar` (Python 3.12, sem dependências).
3. Complete os campos `⟨preencher⟩` do relatório e exporte para PDF.

## Status
- [x] Modelagem da carga e parâmetros
- [x] Roteiro do iSPD e script de análise
- [ ] Executar no iSPD e salvar os `.imsx` e as capturas (**aluno**)
- [ ] Preencher os resultados e a interpretação no relatório (**aluno**)

## Integração com os outros módulos
A carga simulada vem dos módulos reais: fotos do **09-visao-computacional**, sons do **07-iot-ouviai** e conversas do **05-generative-ai** (LLM ajustada com o corpus do **08-nlp**). Todos geram *Ocorrências* (contrato em `CONTEXTO.md`) que o **01-rpa-ia** encaminha. A conclusão sobre escalabilidade entra no documento e no vídeo de **06-governanca** como argumento de viabilidade técnica.
