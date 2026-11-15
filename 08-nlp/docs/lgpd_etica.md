# Ética, segurança e LGPD — Zeladora (assistente de voz)

## 1. Consentimento e transparência
- Antes do primeiro uso, a interface (`app.py`) mostra um aviso: a voz é processada para virar texto, o áudio é apagado em seguida e a resposta é gerada por IA. O botão só funciona com a caixa **"Li e concordo"** marcada (art. 7º, I, e art. 8º da LGPD).
- O assistente se apresenta como **assistente virtual** e não finge ser humano.

## 2. Minimização e retenção
| Dado | O que acontece | Onde |
|---|---|---|
| Áudio da voz (dado pessoal, potencialmente biométrico, art. 5º, II) | Transcrito **localmente** e **apagado** logo depois (`finally` em `stt.py`) | `assistente/stt.py` |
| Texto da pergunta | Fica só na memória da sessão (6 turnos). "Recomeçar conversa" limpa tudo | `Memoria` em `llm.py` |
| Log de latência | Só tempos por etapa e o tamanho da pergunta, **sem conteúdo** | `evidencias/latencia_log.csv` |
| Texto da resposta | Enviado ao edge-tts (Microsoft) para virar voz. Não contém dado do cidadão; para 100% local, use `PiperTTS` | `assistente/tts.py` |

Não se pede nome, CPF nem endereço completo. Para abrir uma ocorrência, o assistente orienta o canal oficial (156/app), que tem a sua própria base legal.

## 3. Limites de atuação
- **Fora do escopo** (política, finanças, piadas etc.): recusa educada e volta ao tema da zeladoria.
- **Saúde:** não orienta; indica o SAMU 192 ou a unidade de saúde.
- **Jurídico:** não dá parecer; indica a Defensoria Pública.
- **Emergência** (árvore caindo em fio, alagamento com risco): manda ligar 193 (Bombeiros) ou 199 (Defesa Civil) **antes** de qualquer outra coisa.

## 4. Alucinação
- O prompt de sistema manda responder **só com o contexto recuperado** da base de conhecimento.
- Se a busca não alcança o limiar de relevância (`LIMIAR_ESCOPO`), o assistente diz que **não sabe** e indica o 156, sem inventar prazos ou valores.
- O baseline extrativo devolve trechos literais da base, o que serve como teto de fidelidade para comparar com as LLMs.

## 5. Voz sintética, sem clonagem
Só são usadas vozes prontas (FranciscaNeural / Piper faber). **Não** há clonagem nem imitação da voz de pessoas reais. A resposta deixa claro que é um assistente virtual.

## 6. Viés do STT (análise)
O Whisper é treinado majoritariamente com áudio da internet, e a literatura mostra WER maior para:
- **sotaques regionais** (Nordeste, interior) e falares fora do "padrão" midiático;
- **pessoas idosas** (voz trêmula, ritmo mais lento), justamente a persona Dona Cida;
- **fala com disartria** ou deficiência de fala;
- **ambiente ruidoso** (rua, TV), comum em periferias.

**Como medimos:** `testes/stt_roteiro.csv` exige pelo menos 3 locutores com perfis diferentes (idade, região, gênero) e 5 áudios com ruído. `avaliar_stt.py` calcula o WER **por locutor e por ruído**, o que deixa a diferença visível.

**Mitigações:** mostrar a transcrição na tela para a pessoa conferir; pedir confirmação de nomes de ruas; modelo `small` em vez de `tiny`; VAD ligado; e sempre oferecer o canal humano (156) como alternativa.

> Smoke test com voz sintética (`evidencias/stt_smoke_sintetico.csv`): WER 0 com o `tiny`. Isso **não** representa voz real; serve só para provar que o pipeline funciona.

## 7. Riscos remanescentes
- O edge-tts depende de serviço externo (termos da Microsoft).
- Os 100% do baseline foram medidos nas mesmas perguntas usadas para ajustar os sinônimos (sobreajuste).
- Os documentos da base são simulados. Em produção, eles teriam que vir da Prefeitura e ser revisados.
