# 03 — Computação Quântica & IA · CitizenTech

**Plataforma CitizenTech de Zeladoria Urbana Acessível**: como a computação quântica ampliaria a solução.

> **Resumo.** O gargalo é a **otimização combinatória da fila e da rota de inspeções**. As ocorrências de buracos e fissuras chegam da Visão Computacional, do chat e do RPA. A capacidade quântica escolhida é a **otimização (QAOA / annealing quântico)**. A **criptografia pós-quântica (PQC)** corre como trilha paralela de segurança e LGPD. Hoje a IA clássica resolve bem. O quântico só fará sentido, de forma realista, a partir de 2030 e em modo **híbrido**.

## 1. Gargalo real do protótipo

Fluxo atual: o cidadão envia a foto → a Visão detecta o dano (com confiança) → o RPA abre o chamado → **a prefeitura precisa decidir quais ocorrências inspecionar, em que ordem e com qual equipe.**

| Por que é gargalo | Detalhe |
|---|---|
| **Explosão combinatória** | Escolher quais das N ocorrências atender hoje gera 2^N combinações. Ordenar a rota gera N! sequências: é um problema de roteamento de veículos com janelas de tempo (VRPTW), que é NP-difícil. |
| **Escala** | No protótipo há dezenas de ocorrências. Numa cidade como São Paulo seriam milhares por dia, centenas de equipes e muitas restrições: prioridade, acessibilidade, trânsito, horário e tipo de equipe. |
| **Lento / caro** | Solvers exatos (MILP) deixam de fechar em tempo útil. Recalcular a cada nova ocorrência urgente (replanejamento dinâmico) custa caro. |
| **Impreciso** | Heurísticas (guloso, OR-Tools, metaheurísticas) dão soluções boas, mas sem garantia. Se o modelo só otimiza distância, ocorrências de bairros periféricos tendem a ficar sempre "para depois". |
| **Inseguro (gargalo secundário)** | Localização, foto e identidade do cidadão trafegam protegidas por RSA/ECC. Esses algoritmos ficam expostos ao ataque "colher agora, decifrar depois" quando surgirem computadores quânticos grandes. |

A demo (seção 5) mostra o efeito: 8 ocorrências dão 256 combinações (trivial); 60 dão 1,15·10¹⁸; 300 dão 2·10⁹⁰.

## 2. Capacidade quântica escolhida

**Principal: otimização quântica.** A fila é formulada como **QUBO**, com variáveis binárias do tipo "inspecionar a ocorrência i" ou "visitar i antes de j". Dois caminhos resolvem a QUBO:
- **QAOA** (Quantum Approximate Optimization Algorithm) em hardware de portas (IBM, Google etc.), num laço **híbrido**: o computador quântico amostra soluções e um otimizador clássico ajusta os ângulos.
- **Annealing quântico** (ex.: D-Wave), que já aceita QUBOs de milhares de variáveis hoje, em modo híbrido.

Por que essa capacidade e não as outras:

| Capacidade | Encaixa? |
|---|---|
| Otimização | **Sim.** O problema é literalmente combinatório: roteamento e seleção sob restrições. |
| Busca (Grover) | Não. O ganho é só quadrático e exige hardware tolerante a falhas. A busca no banco de ocorrências se resolve com índices clássicos. |
| Simulação | Não no núcleo. Serve para química e materiais (ex.: asfalto mais durável), fora do escopo do protótipo. |
| **PQC** | **Sim, como trilha paralela.** Não acelera nada, mas protege os dados do cidadão contra o quântico futuro. Já pode ser aplicada hoje (NIST FIPS 203/204: ML-KEM e ML-DSA). |

**Honestidade técnica:** até hoje não há vantagem quântica comprovada em roteamento real. O roadmap trata o quântico como uma aposta monitorada, com o clássico como baseline obrigatório.

## 3. Roadmap realista

| Fase | Período | O que a IA clássica entrega | O que o quântico agrega | Benefício para o cidadão |
|---|---|---|---|---|
| **0 — Hoje (protótipo)** | 2026 | Priorização por regra (prioridade × confiança da Visão) e heurística gulosa ou OR-Tools para a rota. O modelo QUBO já está escrito e há uma demo de QAOA simulada. | Nada em produção. **PQC:** planejar a migração para TLS híbrido (X25519 + ML-KEM). | Chamados urgentes atendidos primeiro e status transparente no app. |
| **1 — Piloto municipal** | 2027–2028 | MILP/OR-Tools com replanejamento a cada hora, previsão de demanda por bairro (ML) e métrica de equidade territorial na função objetivo. | Benchmark em nuvem (IBM Quantum ou D-Wave híbrido) com dados **anonimizados**, comparado ao clássico. **PQC em produção** (TLS e assinatura de laudos). | Cai o tempo médio até a inspeção, e a periferia deixa de ficar sempre no fim da fila. |
| **2 — Escala metropolitana** | 2029–2031 | Metaheurísticas distribuídas no cluster (disciplina 02) para milhares de ocorrências por dia. | Solvers **híbridos quântico-clássicos** em subproblemas (ex.: grupos de bairros com 50 a 200 variáveis), **só se** o benchmark mostrar ganho de custo, tempo ou qualidade. | Rotas mais curtas permitem mais inspeções por dia, com menos CO₂ e resposta mais rápida a riscos (ex.: buraco numa via usada por cadeirantes). |
| **3 — Quântico tolerante a falhas** | 2032+ | O clássico continua como fallback e auditor. | QAOA e algoritmos variacionais em hardware com correção de erros, replanejando a frota inteira quase em tempo real (inspeção, manutenção e defesa civil). | A cidade responde em horas, não em semanas. A mesma lógica pode ir ao campo (estradas rurais). |

**Critérios de go/no-go para usar o quântico** (contra o hype):
1. qualidade igual ou melhor que a do melhor solver clássico;
2. tempo ou custo menor dentro do mesmo SLA;
3. resultado explicável e auditável;
4. dados anonimizados antes de sair do ambiente da prefeitura.

## 4. Ética, LGPD e ODS ao longo do roadmap

| Fase | Ética | LGPD | ODS |
|---|---|---|---|
| 0 | A função objetivo é explícita e publicada. O peso de prioridade, risco e acessibilidade é decisão pública, não do algoritmo. | Minimização (art. 6º, III): o otimizador recebe só id, tipo, prioridade e coordenada aproximada, **nunca** nome ou foto do cidadão. Base legal: execução de políticas públicas (art. 7º, III, e art. 23). | ODS 11 (cidades) e ODS 9 (infraestrutura). |
| 1 | **Termo de equidade** na QUBO, que penaliza deixar bairros sem atendimento, e auditoria de viés por bairro e renda. | Enviar dados a uma nuvem quântica estrangeira é **transferência internacional** (art. 33): só dados anonimizados ou agregados, com RIPD (art. 38). A PQC protege contra a coleta para decifração futura (art. 46, segurança). | ODS 10 (desigualdades): periferia e pessoas com deficiência priorizadas. |
| 2 | Explicabilidade: toda rota vem com justificativa ("por que OC-X antes de OC-Y"), e o gestor humano pode sobrepor a decisão. | Direito de revisão de decisão automatizada (art. 20). Logs assinados com ML-DSA. | ODS 13 (menos deslocamento e emissões) e ODS 11. |
| 3 | Dependência tecnológica e custo: evitar lock-in em fornecedor quântico e manter um solver clássico aberto. | Governança contínua com a disciplina 06 (KPIs e comitê). | ODS 16 (instituições eficazes e transparentes) e ODS 17 (parcerias). |

## 5. Demo: clássico × quântico simulado

[`demo/demo_qaoa.py`](demo/demo_qaoa.py) usa NumPy puro, sem Qiskit e sem hardware. Ela monta a seleção da fila do dia como **QUBO**: o valor de cada ocorrência é prioridade × confiança, com penalidade por estourar as 6 h da equipe e por juntar ocorrências distantes entre si. Depois resolve de duas formas:
1. força bruta exata (2^8 = 256 estados) e heurística gulosa;
2. **QAOA p=3 simulado** em vetor de estado, com um otimizador clássico no laço (híbrido).

```bash
cd 03-computacao-quantica/demo
python demo_qaoa.py
```

Requisitos: Python 3.12 e NumPy. A saída está registrada em [`demo/saida_demo.txt`](demo/saida_demo.txt).

**Resultado (evidência):**
- O método exato acha o ótimo em cerca de 10 ms.
- O guloso fica cerca de 23% pior no custo.
- O QAOA simulado concentra probabilidade em soluções boas: P(ótimo) ≈ 0,011, cerca de 3× a amostragem aleatória, e as 5 soluções mais prováveis são seleções viáveis próximas do ótimo.
- Mesmo assim, o QAOA **não supera o clássico**.

Essa é exatamente a conclusão do roadmap: hoje o quântico é pesquisa. O valor está em deixar o problema já formulado como QUBO, pronto para testar em hardware quando ele amadurecer.

## 6. Integração com os outros módulos
- **Entrada:** ocorrências no contrato de dados (`dados/ocorrencias.csv`), vindas da Visão (09), do IoT (07), do chat (05) e do RPA (01).
- **Saída:** a fila priorizada e a rota do dia vão para o RPA (01), que encaminha à prefeitura, e para o Front End (04), que mostra o status ao cidadão.
- **Cluster (02):** o replanejamento clássico em escala é a carga que justifica o cluster. O quântico entra como acelerador futuro.
- **Governança (06):** a tabela de ética, LGPD e ODS e os critérios de go/no-go alimentam o documento e o vídeo.

## Referências
- Farhi, E.; Goldstone, J.; Gutmann, S. *A Quantum Approximate Optimization Algorithm*. arXiv:1411.4028, 2014.
- NIST. FIPS 203 (ML-KEM) e FIPS 204 (ML-DSA), 2024.
- BRASIL. Lei nº 13.709/2018 (LGPD).
- ONU. Agenda 2030 — Objetivos de Desenvolvimento Sustentável.
