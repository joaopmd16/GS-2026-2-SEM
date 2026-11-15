<!-- Documento de entrega. Exporte para PDF (Word/Google Docs ou extensão "Markdown PDF" do VS Code).
     Substitua tudo que está entre [colchetes] e insira os prints de evidencias/. -->

# OuviAí – Assistente Sonoro para Acessibilidade
### Módulo IoT da Plataforma CitizenTech de Zeladoria Urbana Acessível

**Disciplina:** Physical Computing, Embedded AI, Robotics & Cognitive IoT
**Global Solution 2026.2 – Tecnólogo em IA – 2TIAP(F-Y)**

| Nome | RM |
|---|---|
| [Nome 1] | [RM] |
| [Nome 2] | [RM] |
| [Nome 3] | [RM] |

Projeto Edge Impulse (público): [https://studio.edgeimpulse.com/public/...]
Vídeo da validação ao vivo: [URL]
São Paulo, novembro de 2026

---

## 1. Problema e contribuição CitizenTech
Cerca de 10 milhões de brasileiros têm algum grau de deficiência auditiva (IBGE). Sinais sonoros do dia a dia, como a campainha ou uma batida na porta, não chegam a essas pessoas. Isso faz perder entregas e visitas e aumenta o isolamento e a insegurança. As soluções comerciais (campainhas luminosas) exigem instalação e custo por dispositivo.

O **OuviAí** usa o que o cidadão já tem: o **celular**. Um modelo de IA embarcado escuta o ambiente, reconhece **campainha**, **batida na porta** ou **ambiente** (nenhum evento) e mostra o resultado na tela, sem enviar áudio para a nuvem.

**Público beneficiado:** pessoas surdas ou com deficiência auditiva, idosos com perda auditiva e pessoas que usam fones ou têm atenção reduzida ao ambiente.

**Contribuição para a plataforma:** o OuviAí é a porta de entrada de acessibilidade da Plataforma CitizenTech. Além do alerta pessoal, eventos detectados podem ser registrados como `Ocorrência` com `origem = "iot"` (seção 9).

## 2. ODS relacionados
- **ODS 10 – Redução das desigualdades** (meta 10.2, inclusão de pessoas com deficiência): tecnologia assistiva sem custo, no aparelho que o cidadão já possui.
- **ODS 11 – Cidades e comunidades sustentáveis** (metas 11.3/11.7, cidade inclusiva): integra o morador com deficiência auditiva à plataforma de zeladoria urbana.
- Complementar: **ODS 3 – Saúde e bem-estar**, pela autonomia e redução do isolamento.

## 3. Arquitetura
```
 Som do ambiente ──► Microfone do celular (16 kHz, mono, PCM16)
                         │  janela 1 s, passo 0,5 s
                         ▼
                Bloco Audio (MFE): espectrograma Mel, 40 filtros
                         ▼
                CNN (Conv1D 8 → Conv1D 16 → Dense softmax 3)
                         ▼
         campainha | batida | ambiente  + probabilidade
                         ▼
   Tela do celular (Edge Impulse "Run this model", navegador)
                         ▼  (evolução)
   Vibração / notificação / flash ──► Ocorrência origem="iot" na Plataforma
```
Toda a inferência roda **no próprio celular** (WebAssembly no navegador); o áudio não sai do aparelho.

**Origem dos áudios:** gravados pelo grupo com o celular conectado ao Edge Impulse, em [nº] cômodos de [nº] residências. Campainha: [real / reproduzida de outro aparelho; descrever]. Batida: porta de [madeira/...]. Ambiente: silêncio, TV, ventilador, passos, torneira.

**Distribuição Training/Test:**
| Classe | Training | Test | Total |
|---|---|---|---|
| campainha | 15 | 5 | 20 × 5 s |
| batida | 15 | 5 | 20 × 5 s |
| ambiente | 15 | 5 | 20 × 5 s |
| **Total** | **45** | **15** | **60 (5 min)** |

As amostras de Test foram gravadas [em outro momento/cômodo] e nunca usadas no treino.

## 4. Coleta e tratamento dos dados
- Padrão: 16 kHz, mono, PCM16, 5 s por amostra; rótulos `campainha`, `batida`, `ambiente`.
- Cada amostra foi ouvida e conferida; [n] amostras foram descartadas e regravadas por [motivo].
- Variação proposital de distância, volume e ruído de fundo para generalizar.
- Nenhuma conversa identificável nas gravações (privacidade/LGPD).

> **[Print 1 – Data acquisition (Training)]** `evidencias/01_data_acquisition_training.png`
>
> **[Print 2 – Data acquisition (Test)]** `evidencias/02_data_acquisition_test.png`

## 5. Modelo de IA – MFE + CNN
### 5.1 Impulse design
Janela de 1000 ms, passo de 500 ms, 16 kHz, zero-pad. Processing: Audio (MFE). Learning: Classification.
> **[Print 3 – Impulse design]** `evidencias/03_impulse_design.png`

### 5.2 Parâmetros MFE
| Frame length | Frame stride | Filtros | FFT | Freq. baixa/alta | Noise floor |
|---|---|---|---|---|---|
| 0,02 s | 0,01 s | 40 | 256 | 0 / 8000 Hz | −52 dB |
> **[Print 4 – MFE / espectrograma]** `evidencias/04_mfe_parametros.png`
>
> **[Print 5 – Generate features / Feature explorer]** `evidencias/05_generate_features.png`

Leitura do feature explorer: [ex.: campainha forma um grupo bem separado (energia em faixas tonais altas); batida e ambiente se sobrepõem em parte, porque batidas fracas lembram ruídos de impacto].

### 5.3 CNN e treinamento
| Ciclos | Learning rate | Validação | Batch | Data augmentation |
|---|---|---|---|---|
| 100 | 0,005 | 20 % | 32 | ruído + máscaras de tempo/frequência (low) |

Arquitetura: Reshape → Conv1D(8, k3) + MaxPool + Dropout 0,25 → Conv1D(16, k3) + MaxPool + Dropout 0,25 → Flatten → Dense(3, softmax).

**Validação:** acurácia [__] %, loss [__]. Desempenho no dispositivo (int8): RAM [__] KB, latência [__] ms.

Matriz de confusão (validação):
| real \ previsto | ambiente | batida | campainha | uncertain |
|---|---|---|---|---|
| ambiente | | | | |
| batida | | | | |
| campainha | | | | |
> **[Print 6 – Classifier]** `evidencias/06_classifier_resultado.png`

## 6. Teste com arquivos inéditos (Model testing → Classify all)
Copie de `teste_arquivos.csv`:
| # | Arquivo Test | Classe real | Classe prevista | Acerto |
|---|---|---|---|---|
| 1 | campainha_test_01 | campainha | | |
| 2 | campainha_test_02 | campainha | | |
| 3 | campainha_test_03 | campainha | | |
| 4 | campainha_test_04 | campainha | | |
| 5 | campainha_test_05 | campainha | | |
| 6 | batida_test_01 | batida | | |
| 7 | batida_test_02 | batida | | |
| 8 | batida_test_03 | batida | | |
| 9 | batida_test_04 | batida | | |
| 10 | batida_test_05 | batida | | |
| 11 | ambiente_test_01 | ambiente | | |
| 12 | ambiente_test_02 | ambiente | | |
| 13 | ambiente_test_03 | ambiente | | |
| 14 | ambiente_test_04 | ambiente | | |
| 15 | ambiente_test_05 | ambiente | | |

**Acurácia de teste:** [__]/15 = [__] %.

Matriz de confusão (teste):
| real \ previsto | ambiente | batida | campainha | uncertain |
|---|---|---|---|---|
| ambiente | | | | |
| batida | | | | |
| campainha | | | | |
> **[Print 7 – Model testing]** `evidencias/07_model_testing.png`

## 7. Validação em tempo real no celular
Deployment → **Run this model** → QR Code → navegador do celular → microfone autorizado.
> **[Print 8 – QR Code / Run this model]** `evidencias/11_qrcode_run_this_model.png`
>
> **[Prints 9 a 11 – Celular classificando campainha, batida e ambiente]** `evidencias/08_celular_campainha.png`, `09_celular_batida.png`, `10_celular_ambiente.png`
>
> **Vídeo:** [URL]

Copie de `validacao_ao_vivo.csv`:
| # | Som produzido | Esperada | Prevista | Prob. na tela | Acerto |
|---|---|---|---|---|---|
| 1 | Campainha | campainha | | | |
| 2 | Campainha | campainha | | | |
| 3 | Campainha | campainha | | | |
| 4 | Campainha | campainha | | | |
| 5 | Campainha | campainha | | | |
| 6 | Batida na porta | batida | | | |
| 7 | Batida na porta | batida | | | |
| 8 | Batida na porta | batida | | | |
| 9 | Batida na porta | batida | | | |
| 10 | Batida na porta | batida | | | |
| 11 | Silêncio | ambiente | | | |
| 12 | TV baixa | ambiente | | | |
| 13 | Passos | ambiente | | | |
| 14 | Torneira | ambiente | | | |
| 15 | Ventilador | ambiente | | | |

**Percentual de acerto ao vivo = acertos ÷ 15 × 100 = [__]/15 = [__] %** (calculado com `python calcular_acerto.py validacao_ao_vivo.csv`).
Falsos positivos na classe ambiente (ambiente → evento): [__]. Eventos perdidos (evento → ambiente): [__].

**Comparação das três avaliações:**
| Avaliação | Dados | Resultado |
|---|---|---|
| (1) Validação do treino | 20 % do Training | [__] % |
| (2) Teste com WAVs inéditos | 15 arquivos Test | [__] % |
| (3) Tempo real no celular | 15 tentativas | [__] % |

A probabilidade mostrada na tela é a **confiança** do modelo em uma janela de 1 s, não a acurácia. A acurácia só se mede comparando as previsões com o rótulo verdadeiro em várias tentativas.

## 8. Discussão dos erros
[Adapte ao que realmente aconteceu. Pontos típicos:]
- **Batida ↔ ambiente:** batidas fracas ou distantes têm pouca energia e se confundem com impactos do ambiente (passos, porta de armário). Mitigação: mais amostras de batidas fracas e de "impactos" rotulados como ambiente.
- **Campainha:** costuma ser a classe mais fácil (tons harmônicos estáveis). Erros aparecem com toques diferentes do treino ou som abafado.
- **Falsos positivos em ambiente:** TV ou música com sons tonais podem virar "campainha". Mitigação: incluir TV/música em `ambiente` e exigir 2 janelas seguidas acima de 0,7 antes de alertar.
- **Queda do teste para o ao vivo:** microfone, distância e acústica do cômodo mudam; o teste ao vivo é o cenário mais realista.

## 9. Inovação, acessibilidade e integração
- **Alerta multimodal:** vibração (`navigator.vibrate`), flash da câmera, notificação push e tela piscando em cor por evento (azul = campainha, laranja = batida), sempre com ícone e texto grande, para não depender só de cor.
- **Smartwatch ou pulseira** recebendo a vibração.
- **Novas classes:** alarme de fumaça, choro de bebê, micro-ondas, sirene na rua.
- **Integração CitizenTech:** com consentimento, cada evento vira uma `Ocorrência` no contrato comum da plataforma (`tipo = "alerta_sonoro"`, `origem = "iot"`, `confianca` = probabilidade), exibida no painel Front End. Numa versão futura, sons urbanos (estrondo de queda de árvore, vazamento) alimentariam a zeladoria e o fluxo RPA para a prefeitura.

## 10. Segurança, privacidade e limitações
- O áudio é processado **localmente** no celular; nada é gravado nem enviado durante a inferência.
- Coleta sem conversas identificáveis e com consentimento dos moradores.
- **Protótipo educacional: não substitui sistemas de segurança ou de alerta de emergência.**
- **Limitações:** dataset pequeno (60 amostras, poucos ambientes, um modelo de campainha); sensível a distância, ruído e microfone; exige o navegador aberto em primeiro plano (bateria); só 3 classes, então sons fora delas caem em "ambiente" ou geram falso positivo; abaixo do limiar de confiança o resultado é "uncertain".

## 11. Conclusão
[2 a 4 linhas: fluxo validado de ponta a ponta, resultados das três avaliações, principal aprendizado.]

## Referências
- EDGE IMPULSE. *Audio classification*. Documentação oficial. Disponível em: https://docs.edgeimpulse.com. Acesso em: nov. 2026.
- IBGE. *Pesquisa Nacional de Saúde 2019*: pessoas com deficiência. Rio de Janeiro: IBGE, 2021.
- ONU. *Objetivos de Desenvolvimento Sustentável*: ODS 10 e ODS 11. Disponível em: https://brasil.un.org/pt-br/sdgs.
