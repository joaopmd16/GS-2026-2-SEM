# CONTEXTO DO PROJETO — GS 2026.2 (FIAP · 2TIAP · IA)

> Arquivo-mestre. Toda sessão de disciplina deve ler isto antes de começar.

## Tema único (obrigatório)
**CitizenTech — Protótipo Integrado com IA para Apoiar o Cidadão.**
"Da cidade ao campo, tecnologia para a vida cotidiana." Soluções com IA centradas
em necessidades reais (inclusão, acessibilidade, sustentabilidade, qualidade de vida),
ligadas a ODS. Pode usar dados reais, simulados ou mockados.

## Nossa solução integrada (conceito)
**Plataforma CitizenTech de Zeladoria Urbana Acessível**: o cidadão (inclusive com
deficiência auditiva) reporta e recebe alertas sobre problemas da cidade; a IA detecta
danos, conversa com o cidadão, encaminha chamados à prefeitura e prioriza inspeções.

ODS principais: **ODS 11** (cidades sustentáveis), **ODS 10** (redução das desigualdades/acessibilidade), ODS 9 (infraestrutura).

## Como cada disciplina se encaixa
| Pasta | Disciplina | Papel no sistema |
|---|---|---|
| `09-visao-computacional` | Visão Computacional | Detecta fissuras/buracos em fotos enviadas pelo cidadão → gera ocorrência com confiança |
| `07-iot-ouviai` | IoT (OuviAí) | Reconhece sons (campainha, batida, ambiente) no celular via Edge Impulse → alerta visual para surdos |
| `05-generative-ai` | Generative AI | Assistente conversacional (RAG) que orienta o cidadão sobre serviços/ocorrências |
| `08-nlp` | NLP | Assistente de VOZ PT-BR (Whisper STT → LLM com memória + base de conhecimento → TTS) para cidadãos com dificuldade de ler/digitar; o pipeline de corpus (conversacional/Q&A/texto puro) alimenta a base de conhecimento |
| `01-rpa-ia` | RPA + IA | Automatiza o fluxo de chamados: lê ocorrências (Pandas/SQL), scraping, APIs, e-mail automático para a prefeitura |
| `04-frontend` | Front End (Streamlit/Gradio) | Interface única que integra os módulos (upload de foto, chat, painel de ocorrências) |
| `02-cluster-computing` | Cluster Computing | Simula no iSPD a carga de processamento de IA da plataforma (ex.: visão + LLM em escala) |
| `03-computacao-quantica` | Computação Quântica | Gargalo: otimização de rotas/fila de inspeções → roadmap quântico (QAOA) + PQC/LGPD |
| `06-governanca` | Governança em IA & BA | Disciplina integradora: vídeo 5–7 min (YouTube não listado), doc ABNT, GitHub com todos os módulos, ética/LGPD, KPIs |

## Contrato de dados compartilhado (usar em todos os módulos)
Entidade **Ocorrência**:
```json
{
  "id": "OC-0001",
  "tipo": "fissura | buraco | alerta_sonoro | outro",
  "origem": "visao | iot | chat | rpa",
  "descricao": "texto",
  "confianca": 0.0,
  "latitude": -23.55, "longitude": -46.63,
  "bairro": "texto",
  "prioridade": "baixa | media | alta",
  "status": "aberta | encaminhada | em_inspecao | resolvida",
  "criado_em": "ISO-8601"
}
```
Base de exemplo: `dados/ocorrencias.csv` (SQLite opcional `dados/citizentech.db`).

## Regras gerais
- Entrega de cada disciplina: **até 19/11/2026 23h55** no Portal do Aluno.
- Pitch integrador (prêmio): vídeo de até 7 min.
- Python 3.12 como padrão. Código de cada disciplina **só na sua pasta**.
- Enunciados originais em `enunciados/`.
- Repo: https://github.com/joaopmd16/GS-2026-2-SEM (privado).
- Cada pasta deve ter README com: objetivo, como rodar, evidências, como integra com os outros módulos.
