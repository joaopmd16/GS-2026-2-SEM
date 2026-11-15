# Passo a passo: execução no iSPD

> Siga **exatamente** os valores de [parametros.csv](parametros.csv). O único valor que muda entre os cenários é o **número de workers** (2 → 4).
> Os nomes de menus podem variar um pouco entre versões do iSPD (3.x). Se um campo tiver outro nome, use o equivalente e anote no relatório.

## 0. Preparação
1. Instale o Java 8+ e baixe o iSPD (site do GSPD/UNESP: `https://gspd.dcce.ibilce.unesp.br/ispd/`). Rode com `java -jar iSPD.jar`.
2. Os modelos serão salvos em `02-cluster-computing/ispd/`.

## 1. Cenário A: 2 workers
1. **File → New** (modelo novo, tipo *Grid/Cluster*).
2. **Ícones na área de desenho** (barra lateral):
   - 1 **Machine** = `Mestre`
   - 2 **Machine** = `Worker1`, `Worker2`
   - 1 **Switch** (ou **Internet**) = `Switch`
   - **Links**: `Mestre–Switch`, `Switch–Worker1`, `Switch–Worker2`.
   > Alternativa equivalente: um único ícone **Cluster** com *Number of slaves = 2*, *Master = sim*, mesma potência, banda e latência. Se usar o ícone Cluster, use-o também no cenário B.
3. **Configurar o Mestre** (duplo clique / painel de propriedades):
   - *Master*: **marcado**
   - *Scheduling algorithm*: **Workqueue**
   - *Computational power*: **50000 MFlop/s**; *Cores*: 1; *Owner*: user1
   - Em *Slaves*, marque **Worker1** e **Worker2**.
4. **Configurar cada Worker**: *Master* desmarcado; *Computational power* **50000 MFlop/s**; *Cores* 1; *Load factor* 0; *Owner* user1.
5. **Configurar cada Link e o Switch**: *Bandwidth* **1000 Mb/s**; *Latency* **0.001 s**; *Load factor* 0.
6. **Users**: confirme que existe só `user1`.
7. **Workload** (menu *Workload* / botão *Add Workload*), tipo **Random**:

   | Campo | Valor |
   |---|---|
   | User / Scheduler | user1 / Mestre |
   | Number of tasks | **1000** |
   | Computing size (Minimum / Average / Maximum) | **10000 / 65000 / 120000** MFlop |
   | Computing probability | **0.5** |
   | Communication size (Minimum / Average / Maximum) | **0.1 / 10 / 20** Mbit |
   | Communication probability | **0.5** |
   | Time of arrival | **0** s |

8. **File → Save as** → `ispd/cenario_A_2workers.imsx`.
9. **Simulate → Simulate** (se pedir, 1 simulação; se houver campo *seed*, use o mesmo valor nos dois cenários).
10. Na janela de resultados:
    - aba **Global**: anote **Total Simulated Time (s)** e salve a captura em `evidencias/A_global.png`;
    - aba **Resources** (ou *Machines*): anote, por worker, as tarefas executadas e o MFlop processado (ou % de uso) e salve em `evidencias/A_resources.png`;
    - se houver gráficos de uso, salve em `evidencias/A_grafico.png`.
11. Capture a tela do modelo desenhado em `evidencias/A_modelo.png`.

## 2. Cenário B: 4 workers
1. Abra `cenario_A_2workers.imsx` e use **Save as** → `ispd/cenario_B_4workers.imsx`. Assim a carga e as configurações ficam idênticas.
2. Adicione `Worker3` e `Worker4` **copiando** o Worker1 (mesmos 50000 MFlop/s) e os links `Switch–Worker3` e `Switch–Worker4` (1000 Mb/s, 0.001 s).
3. No Mestre, marque os 4 workers como *Slaves*. **Não altere a Workload.**
4. Salve, simule e faça as mesmas capturas com o prefixo `B_`.

## 3. Registrar e analisar
1. Preencha [resultados.csv](resultados.csv) com os números do iSPD.
2. Rode `python scripts/analise.py comparar`. O script calcula a redução percentual, T₂/T₄, a eficiência e o desbalanceamento.
3. Copie os números para as tabelas marcadas com `⟨preencher⟩` em [relatorio.md](relatorio.md) e escreva 2–3 frases de interpretação onde indicado.
4. Conferência: `python scripts/analise.py estimar` dá uma estimativa teórica (≈ 669 s com 2 workers e ≈ 336 s com 4). Se o iSPD der algo muito diferente (por exemplo, 10×), revise as unidades (MFlop × GFlop, Mbit × MB).

## 4. (Opcional, enriquece a discussão) Cenário de gargalo de rede
Repita A e B com **Bandwidth = 10 Mb/s** em todos os links, mantendo o resto igual. A comunicação passa a pesar e o ganho de 2→4 diminui. Registre como "análise de sensibilidade", separada da comparação principal.
