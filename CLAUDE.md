# investPass — Painel de Pré-vendas
### Documento de contexto para o Claude Code

---

## 1. Objetivo

Construir uma ferramenta (script + dashboard HTML) que recebe input manual de agendamentos de pré-vendas em texto e gera um painel visual, seguindo a mesma lógica que hoje é feita manualmente num chat do Claude.ai. Não há CRM integrado nessa frente — o input é sempre colado à mão.

Referência visual: depois da primeira versão (tema escuro, ver histórico abaixo), o usuário fez uma rodada extensa de refinamento visual/funcional num mockup separado, fora do Code — `mockup-v3-painel-prevendas.html`, na raiz do projeto. **Esse arquivo é a fonte de verdade de layout** (tema claro, abas, gráficos históricos etc. — ver seção 5, 10 e 11). Os dados dentro dele são fictícios/ilustrativos, não confiáveis como referência de cálculo — só o texto deste documento define as fórmulas.

---

## 2. Formato de input

Uma linha por agendamento:

```
Empresa — DD/MM — Origem — Canal (Agendada por @Pessoa)
```

Com `NO-SHOW` ao final quando aplicável.

Duas listas são coladas separadamente a cada rodada:
- **Realizadas** (ou deveriam ter sido)
- **À realizar**

Quando o mês fecha, tudo migra para Realizadas e a lista de À realizar vem vazia — isso deve ser o sinal de "mês fechado" para a ferramenta (muda formato de exibição de contagem, ver seção 5). A partir da v3, esse sinal por mês é o que decide, mês a mês, se o painel trata aquele mês como aberto ou fechado — nunca a data do sistema (seção 5).

### Exemplo real (fechamento de agosto/2026) — 54 linhas, todas "Realizadas"

```
Grupo Bimbo — 04/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Transpanorama — 04/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Grupo Servopa — 04/08 — LinkedIn Seixas — Ligação (Agendada por @Vinicius Almeida)
Kynetec — 05/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Renault — 05/08 — Associados — Associados (Agendada por @Lucas Pedroso)
FQM — 06/08 — Associados — Associados (Agendada por @Lucas Pedroso)
PetroReconcavo — 06/08 — LinkedIn Raolho — Email (Agendada por @Vinicius Almeida)
Carbel Auto Group — 06/08 — LinkedIn Seixas — Ligação (Agendada por @Vinicius Almeida) NO-SHOW
Fundação Butantan — 10/08 — Associados — Associados (Agendada por @Lucas Pedroso)
OAB Pernambuco — 11/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Mextra Metais — 12/08 — Associados — Embaixadores (Agendada por @Xande) NO-SHOW
Grupo Pereira — 12/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Otis — 12/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Alstom Group — 12/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Grupo Rioto Saúde Ocupacional — 12/08 — Landing Page — WhatsApp (Agendada por @Vinicius Almeida)
Resolv — 12/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Comerc Energia — 13/08 — Associados — Associados (Agendada por @Lucas Pedroso)
SBCD Saúde — 13/08 — Associados — Associados (Agendada por @Lucas Pedroso) NO-SHOW
Lactalis Brasil — 13/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Evolua Energia — 13/08 — Associados — Associados (Agendada por @Lucas Pedroso)
AFDatalink — 13/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Sertran Transportes — 14/08 — LinkedIn Raolho — LinkedIn (Agendada por @Vinicius Almeida)
Icon Solutions do Brasil — 14/08 — LinkedIn Vini — Ligação (Agendada por @Vinicius Almeida)
Moderna Tecnologia — 14/08 — LinkedIn Raolho — WhatsApp (Agendada por @Vinicius Almeida)
Soffner Teconologia — 14/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Celesc — 17/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Camil — 17/08 — Associados — Associados (Agendada por @Lucas Pedroso)
ArcelorMittal — 18/08 — Associados — Associados (Agendada por @Lucas Pedroso)
G4 Educação — 19/08 — Associados — Associados (Agendada por @Lucas Pedroso)
A.C.Camargo Cancer Center — 21/08 — LinkedIn Vini — Email (Agendada por @Vinicius Almeida)
Wobben Windpower — 24/08 — LinkedIn Vini — Ligação (Agendada por @Vinicius Almeida)
SiDi — 24/08 — Lista Fria — Email (Agendada por @Vinicius Almeida)
Capgemini — 25/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Informa Markets — 25/08 — LinkedIn Vini — Ligação (Agendada por @Vinicius Almeida)
Boca Rosa Company — 25/08 — Lista Fria — Email (Agendada por @Vinicius Almeida)
Ticket/Edenred — 25/08 — CONARH — WhatsApp (Agendada por @Vinicius Almeida)
Danone — 25/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Grupo Argenta — 25/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Consórcio Tradição — 25/08 — Associados — Associados (Agendada por @Lucas Pedroso) NO-SHOW
Ploomes — 26/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Lightwall — 26/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Fox Human Capital — 27/08 — LinkedIn Raolho — Ligação (Agendada por @Vinicius Almeida)
LG Lugar de Gente — 27/08 — LinkedIn Vini — Ligação (Agendada por @Vinicius Almeida)
Dr. Ocupacional — 27/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Samsung Eletronics — 27/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Grupo Hub — 27/08 — LinkedIn Seixas — Email (Agendada por @Vinicius Almeida)
BenCorp — 27/08 — CONARH — WhatsApp (Agendada por @Vinicius Almeida)
Cayro Contabilidade — 28/08 — Flash — Ligação (Agendada por @Vinicius Almeida)
Santa Colomba — 28/08 — Associados — Associados (Agendada por @Lucas Pedroso)
Sistel — 28/08 — CONARH — WhatsApp (Agendada por @Vinicius Almeida)
Unimed São Roque — 31/08 — CONARH — Ligação (Agendada por @Vinicius Almeida)
Hospital Ophir — 31/08 — CONARH — WhatsApp (Agendada por @Vinicius Almeida) NO-SHOW
Marsh/Mercer — 31/08 — CONARH — LinkedIn (Agendada por @Lucas Pedroso)
Onfly — 31/08 — Embaixadores — Email (Agendada por @Vinicius Almeida) NO-SHOW
Company Hero — 31/08 — Lista Fria — Ligação (Agendada por @Vinicius Almeida) NO-SHOW
GRT Gratiam — 31/08 — CONARH — Ligação (Agendada por @Vinicius Almeida) NO-SHOW
```

---

## 3. Taxonomia de canais

**Origem do lead — canais próprios (entram na meta de 20):**
LinkedIn Vini · LinkedIn Seixas · LinkedIn Raolho · Lista fria · Landing Page · CONARH · Reengaja

**Origem do lead — canais externos (não entram na meta):**
Associados (renomeada de "Indicação Externa" em 2026-09 — mesmo canal, nome novo) · Flash · Embaixadores

**Atenção**: "Associados" existe tanto como origem (acima) quanto como canal de agendamento (abaixo) — são duas dimensões independentes, e uma call mostrar Origem=Associados e Canal=Associados ao mesmo tempo não é bug nem duplicação, é coincidência de nome confirmada como aceitável. Não "corrigir" isso automaticamente.

**Canal de agendamento (como a call foi marcada — dimensão separada de "origem"):**
LinkedIn · Ligação · Email · WhatsApp · Associados · Referral · Embaixadores

**Apelidos de pessoas** (usados só na seção "Agendamentos por pessoa" e na coluna "Agendada por" da tabela de calls — seção 5; em todo o resto do sistema, o nome completo continua sendo a fonte de verdade):

| Nome completo | Apelido de exibição |
|---|---|
| Vinicius Almeida | Vini |
| Lucas Pedroso | Raolho |
| Lucas Seixas | Seixas |
| Igor Ramos | Igor |
| Xande | Xande |

Qualquer agendador fora dessa lista é exibido pelo primeiro nome.

---

## 4. Regras de negócio

- Meta mensal calibrada: **20 reuniões realizadas via canais próprios**.
- **Envolvimento de pré-vendas (métrica do hero, seção 5) = agendado por Vinicius Almeida, qualquer origem** (própria ou externa) — **não** exige canal próprio. Uma call de canal externo agendada pelo Vinicius (ex: Cayro Contabilidade via Flash) entra normalmente nessa métrica, no hero, no badge/barra/projeção e no cálculo de MTD/esperado. O card "Total de agendamentos (canais próprios)" (seção 5) é uma métrica separada e independente — continua sendo o total de canal próprio de qualquer agendador, não muda com essa regra.
- **No-show pré-vendas**: só conta no-shows de calls agendadas pelo Vinicius — **sem** filtrar por origem própria/externa (já era assim antes e continua igual; ver card "No-show" na seção 5).
- **Lucas Pedroso** gerencia Associados — não conta como pré-vendas. *Atenção: no exemplo real ele também agendou uma reunião via CONARH (Marsh/Mercer, 31/08) — não assumir que Lucas Pedroso só aparece em linhas de origem/canal Associados.*
- CONARH = canal próprio, conta na meta.
- Flash e Embaixadores = externos, não contam na meta.
- Landing Page = canal próprio.
- Calls reagendadas dentro do mesmo mês: contam no mês original.
- Calls reagendadas para outro mês: saem do mês atual e vão para o próximo.
- Dias úteis para MTD: cutoff (usado no label "MTD DD/MM") é o **último dia útil completo anterior a hoje** — pula fins de semana e feriados, retrocedendo até achar um dia útil real. Nunca é o próprio dia de hoje, mesmo que hoje seja dia útil (ex: hoje quinta-feira 03/09 → cutoff é quarta-feira 02/09, não a sexta-feira anterior). **Dias úteis decorridos nunca inclui o dia de hoje** — conta só dias 100% completos, estritamente antes de hoje, até o cutoff. Se o cutoff cair no mês anterior (início do mês, nenhum dia útil completo decorrido ainda no mês corrente), decorridos é 0 — não força a data pro início do mês (isso contaria um dia fantasma). Só se aplica a meses **abertos** (seção 5) — mês fechado não calcula MTD, compara direto com a meta.
- Auto-transição "a realizar" → "realizada" (seção 9): só quando a data da call é estritamente anterior a hoje (`data < hoje`) — nunca no próprio dia da call.
- **"Hoje" é sempre o relógio de quem está olhando a página, calculado no navegador** — não o relógio do servidor no momento em que `gerar` rodou. MTD, dias úteis decorridos e a auto-transição acima (e tudo que depende delas — seção 9) são recalculados a cada carregamento da página e de novo se a aba ficar aberta atravessando a virada do dia. Isso vale também pra determinar se um mês está aberto ou fechado (seção 5): sem "hoje" do servidor mais congelado em `data/*.json`, essa decisão também virou cálculo ao vivo no navegador, e não só os elementos citados na seção 9.

---

## 5. Visualização esperada — aba "Detalhe mensal"

Layout de referência: `mockup-v3-painel-prevendas.html` (seção 1). Duas abas no topo do painel — "Detalhe mensal" e "Histórico" (seção 10) — com um dropdown de mês que só aparece na aba "Detalhe mensal" (escondido na Histórico). **O mês selecionado no dropdown é o que decide se o painel trata aquele mês como aberto ou fechado** (lista "à realizar" vazia = fechado) — nunca a data do sistema.

O dropdown de mês é um **widget customizado** (botão + lista posicionada com `position:absolute; top:100%`), não um `<select>` nativo — decisão deliberada pra garantir que a lista sempre abre pra baixo. Um `<select>` nativo delega a direção de abertura ao navegador (sem controle via CSS), e isso causava a lista abrir pra cima e cobrir o conteúdo acima em telas/viewports mais curtos. Não reverter pra `<select>` nativo sem resolver esse problema de outra forma.

**Mês que abre por padrão**: o mês corrente pelo relógio de quem está olhando a página (mesmo "hoje" ao vivo da seção 4) — **nunca** "o último mês salvo em `data/`". Um mês futuro com uma única call adiantada não pode roubar o default do mês corrente só por ser o arquivo mais recente. Se não houver arquivo salvo pro mês corrente ainda (ex: nenhuma call chegou pra um mês novo), cai pro mês salvo mais recente **anterior** a ele; se nem isso existir (só há meses futuros salvos), cai pro mês salvo mais antigo disponível. Esse cálculo é feito no navegador (`pickDefaultMes` em dashboard.py), no mesmo espírito da seção 4 — `gerar` não fixa esse default a partir do relógio do servidor. Exceção: `gerar --mes YYYY-MM` força explicitamente qual mês abre (uso manual/dev, ex. pra testar um mês específico) — quando passado, esse override vale por cima do cálculo automático.

**Cabeçalho do app** (fixo no topo de toda a página, acima das abas): "investPass | Painel de Pré-Vendas" à esquerda, "última atualização: DD/MM/AAAA HH:MM" à direita (horário em que o `gerar` rodou pela última vez). Não existe mais o título "Agendamentos — [Mês] [Ano]" que ficava antes disso — sem título de mês repetido no meio da página.

**Linha de status do mês** (abaixo do dropdown, acima do hero): se o mês está fechado, texto "Mês encerrado"; se está aberto, `MTD DD/MM · X de Y dias úteis (até DD/MM)`. **Nunca menciona feriados na UI** — feriados continuam usados internamente pra calcular dias úteis (seção 4), mas isso é lógica de cálculo, não aparece escrito em lugar nenhum.

**Hero**:
- Rótulo: "Agendamentos realizados com envolvimento de pré-vendas · Meta = {meta} agendamentos".
- Valor: agendado pela pré-vendas (qualquer origem), realizados e não no-show (seção 4).
- Sem sub-linha abaixo do número/badge — essa informação (realizados/no-shows/a realizar) já está coberta pelos 4 cards abaixo e pelo hover da barra (ver abaixo).
- Badge ao lado do número:
  - Mês fechado: `{cor} {pct}% da meta`, `pct = hero / meta`.
  - Mês aberto: `{cor} {pct}% do MTD ({N} agendamentos)`, `pct = hero / esperado`, `N = esperado` arredondado, `esperado = meta × (dias úteis decorridos / dias úteis totais do mês)`. Nunca usar a palavra "ritmo" nem "esperado:" solto — sempre "MTD".
  - Cor: `<70%` vermelho, `70–90%` amarelo, `>90%` verde — esse threshold vale só para badge/barra/card de projeção do hero. **Não** vale para o card de no-show (fixo em 10%, ver 4 cards abaixo).
- Card de projeção (ao lado do número): rótulo "Projeção final do mês" (aberto) ou "Fechamento do mês" (fechado); valor `{hero + a_realizar} de {meta}`; sub `{hero} realizadas + {a_realizar} a realizar` quando aberto (sem "próprios (pré-vendas)" — já implícito no card), sub vazio quando fechado (nunca escrever "mês encerrado" como sub-texto). **Card sempre neutro** (fundo/borda padrão) — não segue mais a cor de status do badge; só o badge e a barra de progresso (abaixo) carregam a cor de ritmo. Em mês **aberto**, uma linha extra dentro do mesmo card, separada por uma divisória fina (borda superior sutil): "Faltam {faltam} calls · restam {dias} dias úteis" — `faltam = meta − (hero + a_realizar)` (nunca negativo; se a projeção já bate ou passa a meta, o texto vira "Meta coberta pelo agendado"), `dias = dias úteis totais do mês − dias úteis decorridos` (mesmo cálculo do MTD, seção 4). Some em mês **fechado** (não faz sentido "restam dias" nem "a realizar" nesse estado).
- Barra de progresso, escala 0–meta: dois tons da **mesma** cor de status (verde/amarelo/vermelho) — escuro = realizado, claro = a realizar (a realizar já no recorte pré-vendas do hero); nunca dois tons de cores diferentes. Sem segmento/marcador "a realizar" quando o mês está fechado. Marcador triangular (não linha vertical) na posição do valor esperado pelo MTD, com label "MTD - {N}" acima (não "esperado {N}") — só aparece em mês aberto.
- Hover: **na barra**, não no card inteiro — passar o mouse no segmento escuro mostra "{hero} realizadas" num tooltip flutuante; no segmento claro mostra "{a_realizar} a realizar". Dois hovers distintos, um por segmento.

**4 cards, nessa ordem:**
1. "Agendamentos à realizar no mês" (`X` canais próprios · `Y` externos, todo mundo) — **escondido quando o mês está fechado**; quando escondido, os 3 cards restantes ocupam a largura toda (grid de 3 colunas).
2. "No-show" — total e pré-vendas, um bloco em cada ponta do card (esquerda/direita), cada um com `%` grande em cima e o rótulo ("total"/"pré-vendas") embaixo. Cor do número: preto por padrão, **vermelho só se >10%** (threshold fixo, não usa as faixas do hero).
3. "Total de agendamentos (canais próprios)" — número = **soma** de tudo que é canal próprio (realizados + no-shows + a realizar), qualquer agendador; sub `X realizados · Y no-shows` (+ `· +Z a realizar` só quando `Z > 0` — omite esse trecho inteiro quando não há nada a realizar, nunca escreve "+0 a realizar").
4. "Total de agendamentos (canais próprios + externos)" — soma de canais próprios + externos; mesmo formato de sub do card 3 (mesma regra de omitir "+0 a realizar").

Layout interno dos 4 cards: título sempre ancorado no topo (altura reservada fixa, suficiente pro maior título dos quatro, pra nenhum ficar flutuando centralizado quando o texto é curto), valor centralizado verticalmente no meio, sub-texto sempre na mesma altura no rodapé — os quatro cards com a mesma altura total e o mesmo ritmo vertical, independente de quantas linhas cada título ocupa. Hover: sombra sutil no card inteiro (esses 4 cards não têm barra/gráfico interno pra ter hover próprio, ao contrário do hero).

**Breakdown de canais** (duas colunas):
- 🌱 Origem do lead — seções "Canais próprios" e "Canais externos".
- 📲 Canal de agendamento — lista única.
- Cada linha: nome do canal, barra empilhada em **3 tons sóbrios de verde** (não a cor de marca — ver seção 11) — escuro = realizado (sem no-show), médio = a realizar, claro = no-show. A cor não identifica mais o canal, identifica o estágio (isso já está no texto do nome). Só aparecem canais com pelo menos 1 registro no mês. Hover: fundo sutil na linha inteira ao passar o mouse (efeito visual, sem dado novo).
- Contagem: a condição é o **estado do mês** (fechado/aberto), nunca um valor individual sendo zero. Mês aberto → sempre os 3 segmentos `{real} real. | {ar} a real. | {ns} no-show`, mesmo quando algum desses valores é 0 (ex: "0 no-show" continua escrito). Mês fechado → sempre 2 segmentos `{real} real. | {ns} no-show` (a dimensão "a realizar" nem existe nesse estado, por isso some).
- Legenda de cores (realizadas · a realizar · no-show) fixa no rodapé de **cada um** dos dois cards (ancorada embaixo via flexbox — não flutua logo depois da última linha da lista, fica sempre na mesma altura entre os dois cards mesmo quando um tem mais linhas que o outro).
- **Mês com dado histórico incompleto** (ex: meses importados de antes de a origem/canal serem registrados por call — ver nota de proveniência na seção 9): se **nenhuma** call do mês tem origem preenchida, o card "🌱 Origem do lead" inteiro mostra só o texto "dado indisponível" no lugar do breakdown, e a legenda de cores daquele card some junto (o outro card, Canal, segue a mesma regra de forma independente — um pode estar disponível e o outro não no mesmo mês). Isso é diferente de "canal com 0 registros" (que já não aparece, regra acima) — aqui é a dimensão inteira que não tem dado em nenhuma linha do mês.

**👤 Agendamentos por pessoa** (vem logo após Origem/Canal — as tabelas de calls abaixo são o último elemento da página): barra com os mesmos 3 tons sóbrios de verde (realizadas · a realizar · no-show), nomes de exibição = apelidos (seção 3). Contagem segue a mesma regra do breakdown (3 segmentos sempre no mês aberto, 2 no mês fechado — condição pelo estado do mês, não por valor zerado). Hover de fundo sutil na linha, igual ao breakdown. Legenda de cores fixa abaixo do bloco.

**Tabela(s) de calls** — substitui o antigo formato de lista por dia. Mesmo componente de tabela nos casos abaixo (colunas: Data, Empresa, Origem, Canal, Agendada por (apelido, seção 3), e uma tag "NO-SHOW" quando aplicável):
- Mês fechado: **uma única tabela**, título "Todas as calls de {mês}", todas as calls do mês.
- Mês aberto: **duas tabelas**, nessa ordem:
  1. "Pipeline restante do mês ({Mês}/{Ano}) · N calls a realizar" — todas as calls "a realizar" **do mês inteiro** selecionado (não mais só a semana corrente).
  2. "Calls já realizadas no mês ({Mês}/{Ano}) · N calls realizadas (ou que deveriam ter sido)" — só as calls já realizadas até agora nesse mês, no-shows incluídos (com a tag). Existe só no mês aberto — no mês fechado a tabela única acima já cobre tudo, não duplicar.
- Campo ausente (data, origem ou canal) numa call específica vira só "—" na célula correspondente, sem texto de aviso — diferente da regra acima (que é o card/breakdown inteiro faltando quando a dimensão inteira do mês não tem dado); aqui é célula a célula, mesmo num mês onde a dimensão está disponível para outras calls.
- Container com scroll (`max-height`, header fixo) — nunca despejar todas as linhas sem scroll.
- **Sem hover nas linhas** — diferente do breakdown e do "Agendamentos por pessoa" acima.

---

## 6. Confirmações que devem ser feitas antes de processar

O processo manual hoje sempre passa por 3 checagens antes de consolidar os dados — a ferramenta deve replicar isso como validação/aviso, não como bloqueio silencioso:

1. **Duplicatas** (mesma empresa, datas diferentes)
2. **Origens/canais novos** não vistos antes na taxonomia
3. **Calls que sumiram** vs a versão anterior processada (reagendamento ou cancelamento?) — precisa de algum estado persistido entre rodadas (arquivo local, ex. `data/ultimo-processado-AAAA-MM.json`) pra comparar contra a rodada atual.

---

## 7. Observações da amostra real de agosto (para o parser/taxonomia)

Rodando a taxonomia acima contra os dados reais, aparecem pontos que a spec verbal não cobria:

1. **Correção de dado**: a linha do Grupo Rioto Saúde Ocupacional (12/08) tinha origem "Inbound" e canal "Ligação" registrados errado — o correto é **Origem = Landing Page, Canal = WhatsApp** (já corrigido no exemplo da seção 2). Isso valida que a checagem de "origem/canal não reconhecido" (seção 6, item 2) tem valor real: foi ela que pegou esse erro de digitação. O Claude Code deve manter essa validação ativa mesmo no fluxo incremental (seção 9) — todo novo input, seja avulso ou em lote, passa por ela.
2. **Variação de capitalização**: "Lista Fria" aparece nos dados reais, mas a taxonomia da seção 3 lista "Lista fria" (minúsculo). O parser precisa normalizar por case-insensitive pra não tratar como origem desconhecida.
3. **Lucas Pedroso não é exclusivo de origem/canal Associados** — a linha `Marsh/Mercer — 31/08 — CONARH — LinkedIn (Agendada por @Lucas Pedroso)` mostra ele agendando via CONARH também. Não codificar regra implícita de "pessoa X = canal Y".

Esse fechamento de agosto é só **Realizadas** (54 linhas, sem "À realizar") — bom caso de teste pro modo "mês fechado".

---

## 8. Formato alternativo de input — mensagem do Slack

Além do formato compacto (seção 2), o usuário quer poder colar diretamente a mensagem que já sai no canal do Slack quando uma call é agendada, sem reformatar à mão. Exemplo real:

```
Lucas Pedroso  [18h35]
NOVA CALL AGENDADA 

 Data da reunião: 18/09 - 14h
 Contato: Erica Sá
 Cargo: Analista Remuneração e Benefícios
 Empresa: São Martinho
 Origem do lead: indicação externa
 Canal de agendamento: associada - Camila Martins
 Vendedor: [@Lucas Pedroso](https://invest-ai-workspace.slack.com/team/U021RCUQ02C)
 Link do Pipedrive: https://investai.pipedrive.com/deal/3971
```

**Mapeamento de campos** (Slack → modelo interno):

| Campo Slack | Campo interno | Observação |
|---|---|---|
| `Empresa` | empresa | — |
| `Data da reunião` | data | Vem com hora (`18/09 - 14h`) — **decidido: descartar a hora**, guardar só a data, igual ao formato compacto |
| `Origem do lead` | origem | Minúsculo (`indicação externa` — exemplo anterior à renomeação da seção 3; hoje essa origem se chama `Associados`) — normalizar case-insensitive contra a taxonomia da seção 3 |
| `Canal de agendamento` | canal | Vem com sufixo (`associada - Camila Martins`) — `associada` mapeia para `Associados`; o texto depois do traço é o nome de quem indicou/associou. **Decidido: descartar**, não guardar como metadado |
| `Vendedor` | agendadoPor | Equivalente ao "Agendada por @Pessoa" do formato compacto |
| `Link do Pipedrive`, `Contato`, `Cargo` | — (descartados) | **Nunca extraídos nem persistidos, por design — não é "campo opcional que fica vazio", é campo que o parser ignora deliberadamente.** `data/*.json` é público (seção 13): nome de contato, cargo e o ID do Pipedrive (que junto com a URL identifica o negócio no CRM) não têm uso na fórmula/dashboard e não devem vazar pro repositório. O parser do Slack extrai só empresa/data/origem/canal/agendadoPor — os mesmos campos que o formato compacto já usa — e o texto bruto da mensagem (que conteria essas linhas) também não é guardado no campo `raw` da call. Desambiguação de calls (seção 9) usa só empresa + data. |
| Nome de quem postou + horário (`Lucas Pedroso [18h35]`) | — | Normalmente igual ao campo `Vendedor` — não usar como fonte de verdade, é só o autor da mensagem no Slack |

O parser deve aceitar **os dois formatos simultaneamente** (compacto e Slack) e converter ambos pro mesmo modelo interno antes de calcular qualquer métrica.

---

## 9. Modelo de atualização incremental

Hoje o usuário sobe a lista completa a cada rodada. O pedido é trocar isso por um modelo de **estado persistido + comandos pontuais**, parecido com um agente conversacional que vai atualizando um banco de dados local:

- **Estado**: lista mestra por mês (ex: `data/2026-09.json`), cada call com status (`a_realizar` / `realizada`) e flag `no_show`. Essa lista é a fonte de verdade — o dashboard é sempre gerado a partir dela, nunca do texto colado diretamente.
- **Comando "nova call agendada"**: cola uma mensagem (formato compacto ou Slack, seção 8) → parseia → adiciona à lista mestra com status `a_realizar`.
- **Comando "call X foi no-show"**: identifica a call (por empresa, e por data se houver ambiguidade) → muda status para `realizada` + `no_show = true`.
- **Regra automática de virada de status — calculada no navegador, não persistida**: qualquer call com status `a_realizar` cuja data já passou (`data < hoje`, seção 4) e que não foi marcada como no-show é **exibida** como `realizada` (sem no-show) automaticamente — sem exigir comando explícito do usuário pra isso, e sem precisar rodar `gerar` de novo. Mas isso é só uma decisão de exibição: `data/*.json` continua guardando o status **literal** que foi salvo (`a_realizar`) — o arquivo nunca é reescrito por causa da data passar, só por comando explícito (`import`, `no-show`, `mudar-data`). `gerar` embute em `docs/index.html` a lista de calls de cada mês tal como está salva; quem aplica a transição é o JavaScript da página, no carregamento (e de novo se a aba ficar aberta atravessando a virada do dia), usando o relógio de quem está olhando. Roda para **todos** os meses com dado salvo, não só o mês selecionado no momento (seção 10 precisa disso pra ficar sempre correto) — inclusive a própria determinação de "mês fechado" (seção 5) passa a depender dessa transição ao vivo, já que fechado = zero calls com status efetivo `a_realizar` depois de aplicá-la.
- **Comando "mudou a data da call X"**: identifica a call e atualiza o campo `data` in-place, mantendo o resto do registro.

**Implicação de design**: como os comandos de update (no-show, mudança de data) precisam identificar uma call específica, `empresa` sozinho pode ser ambíguo (duas calls da mesma empresa em datas diferentes, por exemplo). Usar `empresa + data` — não há `pipedriveId` persistido pra desambiguar (seção 8: descartado deliberadamente, `data/*.json` é público) — e pedir confirmação ao usuário se houver mais de um match.

Isso substitui a checagem de "calls que sumiram vs. versão anterior" (seção 6, item 3) — que fazia sentido no modelo de "sobe a lista inteira toda vez" — por um modelo onde a lista mestra nunca é sobrescrita por inteiro, só mutada por comando. Vale manter a validação de duplicata e de origem/canal desconhecido (seção 6, itens 1 e 2) rodando a cada novo registro adicionado.

**Campo `origemTipo`** (própria/externa) fica gravado explicitamente em cada call, separado do campo `origem` (o texto/nome do canal). O parser sempre preenche os dois juntos a partir do mesmo valor de origem — mas o motivo de existirem separados é permitir meses com dado histórico incompleto (ver nota de proveniência abaixo) onde `origem` fica `null` mas a classificação própria/externa continua confiável e é usada pra meta, hero, e os cards de "Total de agendamentos" (seção 5). **Nunca re-derivar `origemTipo` a partir do texto de `origem`** quando `origem` for `null` — nesse caso não tem como, e é exatamente pra isso que o campo existe separado.

**Proveniência dos dados de Jan–Set/2026**: importados em 2026-09 a partir de uma planilha de conferência fornecida pelo usuário (não pelo fluxo normal do parser/CLI), com níveis de completude diferentes por mês, validados contra uma aba "Resumo" com totais por fórmula:
- Jan–Mar: `origem` e `canal` ficam `null` (dado não confiável na fonte); `origemTipo` vem de uma coluna de categoria própria/externa separada, que é confiável.
- Abr: `origem` disponível, `canal` e `data` ficam `null`.
- Mai–Jun: `origem` e `data` disponíveis, `canal` fica `null`.
- Jul–Set: dado completo (origem, canal, data, agendado por, no-show).

Isso é só histórico dessa importação pontual — não é uma regra permanente do parser (que sempre popula todos os campos a partir do texto colado). A regra permanente é a de "dado indisponível" na seção 5 e a de janela por gráfico na seção 10, que lidam com qualquer mês (passado ou futuro) onde `origem`/`canal` estejam `null` em todas as calls.

---

## 10. Aba "Histórico"

Sem dropdown de mês (escondido, seção 5). Agrega todos os meses com dado salvo em `data/`, limitado aos últimos 12 (cronológico) — **nunca mostrar mês futuro vazio/placeholder** nos eixos, só entram meses que realmente têm arquivo salvo.

Sem chip de "meta batida" no topo (removido — não faz mais parte da aba).

**Regras gerais dos 5 gráficos de linha** (no-show, pré-vendas MoM, origem, canal, pessoa):
- Linhas finas, bolinhas pequenas. Hover: o ponto/barra sob o mouse ganha um destaque visual sutil (bolinha cresce um pouco, barra clareia), além do tooltip com o valor.
- Nada de número pontual fixo na tela — valor de cada ponto só aparece em hover/tooltip.
- Eixo Y discreto: 3–4 marcações, cor neutra/clara, não compete visualmente com os dados.
- Linhas de referência (meta, meta de no-show) discretas — **sem texto solto dentro da área do gráfico** (isso não escala com mais meses no eixo X). O label da linha de referência vira item de legenda, junto dos outros itens (ex: "meta de no-show: 10%", "meta de agendamentos: {N}"), com um swatch tracejado pra diferenciar de série de dado real. O texto do hover de cada segmento (ex: "agendado pela pré-vendas", "sem envolvimento de pré-vendas") tem que usar exatamente a mesma palavra da legenda correspondente.
- A escala do eixo Y é sempre dinâmica em função do maior valor da série — nunca um teto fixo (isso causava a linha de no-show vazar pra fora da área do gráfico quando um mês passava do teto hardcoded).
- Título do card sozinho, sem subtítulo/descrição embaixo.
- **Projeção do mês corrente (aberto) nos gráficos de VOLUME**: "Performance de pré-vendas MoM", "Performance por Origem MoM", "Performance por Canal MoM" e "Performance por Pessoa MoM" usam realizado + a realizar como valor do ponto/barra do mês aberto (mês fechado tem "a realizar" = 0, então o valor não muda). Marcação visual de que é projeção: "*" no label do eixo X desse ponto/barra + "(projeção)" no tooltip; nos gráficos de linha, o segmento final (penúltimo → último ponto) é tracejado. **Exceção: "Taxa de no-show ao longo dos meses" NÃO projeta** — no-show só existe depois que a call acontece, então esse gráfico usa só o que já foi realizado, sem marcação de projeção.

**5 cards** (todos os meses disponíveis, abertos ou fechados, entram — não há mais filtro de "fechado" na aba Histórico):

1. **Taxa de no-show ao longo dos meses** — linha: no-show total % e no-show pré-vendas % (mesmas métricas do card "No-show" da seção 5, sem filtro de origem própria), com linha de referência em 10% (label "meta de no-show: 10%").
2. **Performance de pré-vendas MoM** — barra empilhada, **todos os canais** (próprios + externos, não só própria): segmento "Agendado pela pré-vendas" (Vinicius, qualquer origem, realizado e não no-show, projetado no mês aberto — regra geral acima) + segmento "Sem envolvimento de pré-vendas" (total de calls do mês, qualquer canal/agendador, menos o segmento acima, também projetado) — **excluindo no-shows** dos dois segmentos (o no-show já tem gráfico próprio no item 1). Esse "pré-vendas" usa a mesma definição ampliada do hero da seção 5 (agendado por Vinicius, qualquer origem) — os dois coincidem desde a revisão da seção 4. Linha de referência na meta mensal (seção 4), como item de legenda (regra geral acima). Espaçamento das colunas proporcional à quantidade de meses no período, não esticado pra ocupar a largura toda com poucos meses.
3. **Performance por Origem MoM** — linha, uma série por origem, **próprias e externas juntas** (antes só entravam as próprias), só as origens com pelo menos uma call (realizada ou a realizar) em algum mês do período. **Meses sem nenhum dado de origem (seção 5, "dado indisponível") ficam de fora do eixo X inteiro** — mesma lógica do "nunca mostrar mês futuro vazio" no topo desta seção, mas por disponibilidade de dado em vez de existência do arquivo.
4. **Performance por Canal MoM** — mesmo formato do item 3, mas por canal de agendamento; mesma regra de excluir do eixo X os meses sem nenhum dado de canal.
5. **Performance por Pessoa MoM** — mesmo formato, uma série por pessoa (apelidos da seção 3).

---

## 11. Paleta e referência visual

Fonte de verdade de layout: `mockup-v3-painel-prevendas.html` (raiz do projeto) — usar como referência direta de HTML/CSS/JS, não só como inspiração. Trocou o tema escuro da primeira versão por um tema **claro**:

- Fundo do painel: `#F1F5F8`. Cards: `#FFFFFF`.
- Verde de marca (`#0ED555`) **só** nos elementos de destaque principal do hero: barra de progresso, badge de status quando verde, card de projeção quando verde. Quando o status é amarelo/vermelho, badge/barra/card de projeção usam as cores de amarelo/vermelho correspondentes (não verde) — ver mockup (`--amber`, `--red` e suas variantes `-bg`).
- Todo o resto que usa verde — breakdown de canais, por pessoa, segmentos dos gráficos do histórico — usa tons de verde **sóbrios/dessaturados** (`--g-dark` / `--g-mid` / `--g-pale` no mockup), nunca o verde de marca vibrante. A cor aí não identifica canal, identifica estágio (realizado/a realizar/no-show).
- Fonte: Montserrat (Google Fonts, como no mockup) ou fallback sans-serif equivalente.

---

## 12. Escopo explícito

- **Sem CRM/API integrada para leitura automática** — input de novas calls continua manual (colado pelo usuário), mas agora em dois formatos aceitos (seção 8) e com mutação incremental (seção 9), não mais reenvio da lista completa.
- **Com persistência real**: a lista mestra por mês (seção 9) é o dado principal do sistema, não um cache descartável — precisa sobreviver entre sessões do Claude Code.
- **Um único arquivo de dashboard** (`docs/index.html`, seção 13), não mais um arquivo por mês — a partir da v3, o dropdown de mês (seção 5) e a aba Histórico (seção 10) exigem ter todos os meses disponíveis na mesma página, com troca de mês/aba no client-side (JS), sem regerar/recarregar. O comando `gerar` (seção 9) processa todos os meses salvos em `data/` de uma vez e embute os dados no HTML.
- Plataforma alvo: **Claude Code**, não artifact do claude.ai.

---

## 13. Publicação via GitHub Pages

- **Repositório**: [`wallace-investpass/investpass-pre-sales-pannel`](https://github.com/wallace-investpass/investpass-pre-sales-pannel), público, dedicado (não reaproveita o `investpass-conversion-dashboard`, que é outro projeto — app Python/Heroku pra Conversion Intelligence).
- **Link do painel (GitHub Pages)**: **https://wallace-investpass.github.io/investpass-pre-sales-pannel/** — esse é o link fixo pra compartilhar com o time e usar no report semanal do Slack.
- **`data/*.json` é versionado** (removido do `.gitignore` em 2026-09) — a lista mestra por mês vai pro mesmo repositório público do dashboard, e o commit/push de `gerar --push` inclui tanto `docs/index.html` quanto `data/`. Isso dá backup automático da lista mestra via git (antes só existia na máquina local).
- **Privacidade por design**: o parser (compacto e Slack, seção 8) nunca extrai nem persiste `contato`, `cargo` ou `pipedriveId` — só empresa, data, origem, canal, agendado por e no-show chegam a `data/*.json`. Isso é deliberado justamente porque `data/` é público (item acima): não existe campo "opcional" que possa vazar nome de contato, cargo ou ID do Pipedrive, porque esses campos nunca são capturados em primeiro lugar.
- **Pages**: "Deploy from a branch", branch `main`, pasta `/docs` (sem step de build — o HTML gerado já é o artefato final).
- **Publicação automática**: `python3 cli.py gerar --push` gera `docs/index.html` e, se houver mudança, faz `git add docs && git commit && git push` sozinho — é o comando usado sempre que uma atualização real (não teste/dev) precisa ir pro ar. `gerar` sem `--push` só atualiza o arquivo local, sem tocar no git (usado pra iteração/teste).
