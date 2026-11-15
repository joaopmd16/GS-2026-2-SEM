# Guia passo a passo – OuviAí no Edge Impulse

Fluxo: **som do ambiente → microfone do celular → MFE → CNN → classe na tela do celular**.
Tempo estimado: 2h30 (coleta 1h, treino 30 min, testes e prints 1h).

> 📸 = tire print e salve em `evidencias/` com o nome indicado.

## 0. Preparação
- Conta gratuita em <https://studio.edgeimpulse.com>. **Create new project** → nome `OuviAi-CitizenTech`.
- Celular com Chrome (Android) ou Safari (iOS), carregado, na mesma internet.
- Material: campainha real **ou** som de campainha tocado de *outro* aparelho (caixa de som), uma porta para bater e um ambiente doméstico normal.
- Privacidade: grave sem conversas ao fundo. Se alguém falar, descarte a amostra.

## 1. Coleta (Data acquisition)
1. **Devices → Connect a new device → Use your mobile phone** → leia o QR Code com o celular → autorize o microfone.
2. No celular aparece *Data collection*. Configure no Studio (aba Data acquisition):
   - **Label**: `campainha`, `batida` ou `ambiente` (sempre minúsculas e sem acento — o mesmo nome nas 3 etapas).
   - **Sample length**: `5000` ms. **Frequency**: 16000 Hz (padrão do celular no EI).
3. Grave **20 amostras de 5 s por classe** (60 no total). Dicas para variar e generalizar:
   | Classe | Como gravar | Variar |
   |---|---|---|
   | campainha | 1–2 toques dentro dos 5 s | distância 1 m / 3 m / outro cômodo, volume, 2 tons diferentes |
   | batida | 2–4 batidas com os nós dos dedos | força, porta de madeira/metal, ritmo |
   | ambiente | nada de campainha nem batida | silêncio, TV baixa, ventilador, torneira, passos, rua ao fundo |
4. **Divisão Training/Test**: mantenha **15 em Training e 5 em Test por classe**. Opção mais segura: grave as 5 últimas de cada classe já com a aba **Test data** selecionada (*Collect data → Category: Test*) em outro dia/horário/cômodo. Não use **Perform train/test split** depois de mover manualmente. **Nunca mova uma amostra de Test para Training.**
5. Abra cada amostra e ouça (▶). Se o evento não estiver lá, apague e regrave. Se o evento ocupar só 1 s, tudo bem — a janela deslizante cuida disso.
6. 📸 `01_data_acquisition_training.png` (lista + barra Train/Test 75/25) e `02_data_acquisition_test.png`.

> Padronização: o Edge Impulse grava em **16 kHz, mono, PCM16**. Se usar WAVs externos, converta antes:
> `ffmpeg -i entrada.mp3 -ac 1 -ar 16000 -sample_fmt s16 saida.wav`

## 2. Impulse design (Create impulse)
| Bloco | Parâmetro | Valor sugerido | Por quê |
|---|---|---|---|
| Time series data | Window size | **1000 ms** | campainha e batida duram < 1 s |
| | Window increase (stride) | **500 ms** | ~9 janelas por amostra de 5 s → mais dados de treino |
| | Frequency | 16000 Hz | exigido |
| | Zero-pad data | ✔ | |
| Processing block | **Audio (MFE)** | — | espectrograma Mel, bom para sons não-vocais |
| Learning block | **Classification** (Keras) | — | CNN |

Clique **Save Impulse**. 📸 `03_impulse_design.png`.

## 3. MFE (parâmetros e Generate features)
| Parâmetro | Valor |
|---|---|
| Frame length | 0.02 s |
| Frame stride | 0.01 s |
| Filter number | 40 |
| FFT length | 256 |
| Low frequency | 0 Hz |
| High frequency | 8000 Hz (Nyquist de 16 kHz) |
| Noise floor | −52 dB |

Opcional: **Autotune parameters** e compare. Depois **Save parameters → Generate features**.
O *Feature explorer* deve mostrar 3 nuvens razoavelmente separadas; `batida` e `ambiente` tendem a se misturar — normal.
📸 `04_mfe_parametros.png` (espectrograma) e `05_generate_features.png` (feature explorer).

## 4. Classifier (CNN)
Configurações de treino:
| Parâmetro | Valor |
|---|---|
| Number of training cycles | **100** |
| Learning rate | **0.005** |
| Validation set size | 20 % |
| Batch size | 32 |
| Data augmentation | ✔ Add noise: *Low*; ✔ Mask time bands: *Low*; ✔ Mask freq bands: *Low* |
| Profile int8 | ✔ |

Arquitetura (padrão do EI para áudio – mantenha):
```
Input (MFE 99x40)
Reshape (40 colunas)
Conv1D 8 filtros, kernel 3, ReLU → MaxPool1D 2 → Dropout 0.25
Conv1D 16 filtros, kernel 3, ReLU → MaxPool1D 2 → Dropout 0.25
Flatten → Dense(3, softmax)
```
Clique **Start training**. Anote acurácia de validação, loss e matriz de confusão.
- Se acurácia < 80 %: aumente ciclos para 200, ou acrescente uma camada Conv1D de 32 filtros (botão "Add an extra layer"), ou colete mais amostras variadas da classe mais confundida.
- Se treino ≈ 100 % e validação baixa: overfitting → mais dados / mais dropout.
📸 `06_classifier_resultado.png` (acurácia + matriz de confusão + on-device performance).

## 5. Model testing (WAVs inéditos)
**Model testing → Classify all**. Registre em `teste_arquivos.csv` a classe prevista de cada um dos 15 arquivos (clique em ⋮ → *Show classification* para ver o resultado por amostra).
```
python calcular_acerto.py teste_arquivos.csv
```
📸 `07_model_testing.png` (acurácia de teste + matriz).

## 6. Deployment no celular e validação ao vivo (obrigatório)
1. **Deployment → Run this model / Launch in browser** (ou ícone de QR Code no Dashboard → *Run this model*).
2. Leia o QR Code com o celular, abra no navegador, permita o microfone. A tela mostra a classe e as probabilidades a cada janela.
3. Faça **5 tentativas por classe (15)**. Para cada tentativa: produza o som, espere ~2 s, anote a classe que dominou na tela em `validacao_ao_vivo.csv` (coluna `classe_prevista`; opcional: `probabilidade_exibida` como 0.87).
   Use situações **novas** (outro cômodo/distância) – é a avaliação mais honesta.
4. Grave um vídeo curto (30–60 s) com a tela do celular + o som sendo produzido, ou capturas: 📸 `08_celular_campainha.png`, `09_celular_batida.png`, `10_celular_ambiente.png`, `11_qrcode_run_this_model.png`.
5. Calcule:
```
python calcular_acerto.py validacao_ao_vivo.csv
```
   O script imprime **acertos/15 e o %**, a matriz ao vivo e os falsos positivos na classe ambiente; copie para o documento de entrega.

## Três avaliações – não confundir
| # | O que é | Onde | Métrica |
|---|---|---|---|
| 1 | Validação do treino | Classifier (20 % do Training) | acurácia de validação |
| 2 | Teste com WAVs inéditos | Model testing (5/classe) | acurácia de teste |
| 3 | Tempo real no celular | Run this model (15 tentativas) | % de acerto = acertos/15 |

**A probabilidade exibida na tela não é a acurácia** — é a confiança do modelo naquela janela.
