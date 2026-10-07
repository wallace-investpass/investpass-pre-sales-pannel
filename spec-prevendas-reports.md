# investPass — Pré-vendas Reports (Slack)
### Documento de especificação v3 — versão final consolidada, 2026-09-04 (atualizada em 2026-10-07: Check Diário e migração do cron pro Railway)

Reconcilia a spec v1 original com as correções feitas em conversas subsequentes e com o comportamento real implementado em `src/reports.py`, `src/calc.py`, `src/slack.py`, `cli.py`, `config/slack_reports.json` e `.github/workflows/`. Onde a v1 divergia do código, o código venceu — ver §9 (histórico de correções) para o que mudou e por quê.

---

## 1. Contexto e objetivo

Três reports automatizados no Slack (os dois primeiros no canal, o terceiro em DM; ver §11), derivados do painel "investPass — Pré-vendas Intelligence" (`CLAUDE.md`), complementando-o da mesma forma que o Weekly Sales Report complementa o Conversion Intelligence Dashboard (`spec-weekly-sales-report.md`):

1. **Weekly Report** — toda segunda-feira, ritmo da semana em andamento dentro do mês corrente.
2. **Fechamento Mensal** — todo dia 1, placar final do mês que acabou de fechar.
3. **Check Diário** — dias úteis, DM pro Vinicius com as calls de hoje agendadas por ele (§11).

Público duplo: útil pro Vini (pré-vendedor, precisa saber onde focar) e pro restante do time (entender se o envolvimento da pré-vendas está alimentando o funil de vendas no ritmo esperado, independentemente do canal de origem da reunião). Tom direto, sem rodeio — mesmo padrão do Weekly Sales Report.

Ao final de cada report: link para o painel completo, pra quem quiser aprofundar.

---

## 2. Fonte de dados

**Diferente do Weekly Sales Report**: não vem do Postgres/Supabase. A fonte é o **JSON stateful mensal** do painel de Pré-vendas (armazenamento incremental por mês — add call / marcar no-show / mudar data, conforme especificado no `CLAUDE.md`). O job de cada report lê esse JSON diretamente; não há schema de banco relacional envolvido aqui.

Ambos os jobs reaproveitam a mesma lógica de cálculo já usada pelo painel (hero metric, MTD, thresholds de cor, taxa de no-show) — não reimplementar essas regras em paralelo.

**Implementado**: como o painel calcula tudo isso em JS, ao vivo, no navegador (porque depende do relógio de quem está olhando a página), e os reports rodam num cron sem ninguém olhando, não dá pra literalmente compartilhar código entre os dois runtimes. A solução foi portar a lógica pra Python num módulo próprio (`src/calc.py`), que é a fonte única usada pelos dois jobs — qualquer mudança de regra de negócio que afete o painel (MTD, thresholds, no-show, meta) precisa ser replicada manualmente lá também.

---

## 3. Disparo

| Report | Cadência | Trigger |
|---|---|---|
| Weekly Report | Toda segunda-feira, 8h (horário de Brasília) | Cron semanal, mesmo horário do Weekly Sales Report |
| Fechamento Mensal | Todo dia 1 do mês, corrido (não precisa ser dia útil) | Cron mensal fixo no dia 1 — reporta o mês que fechou (mês anterior à data de disparo) |
| Check Diário | Dias úteis, 8h (horário de Brasília) | Cron seg–sex, DM pro Vinicius (§11) |

**Canal Slack**: `C09UJ55HQHW` — canal **dedicado de Pré-vendas**. Este é o valor correto e definitivo, não um ajuste temporário: a v1 desta spec errava ao dizer "mesmo canal do Weekly Sales Report" (`C09TLCZB88M`, que é o canal de **Vendas**) — os dois são canais distintos. O erro só foi percebido no primeiro disparo real de produção (Fechamento de Agosto/2026), que saiu no canal errado por engano; a mensagem indevida ficou pendente de remoção manual (ver pendência em §9).

**Mecanismo de disparo (desde 2026-10-07)**: **Railway**, projeto `prevendas-reports` (separado do projeto de Vendas, `vendas-reports`), três serviços cron — todos em imagem `python:3.11`, sem repo conectado: cada execução faz `git clone --depth 1` da `main` e roda o `cli.py`, então sempre usa o `data/` e o código mais recentes, sem depender de redeploy a cada push:
- `weekly-report` — `0 11 * * 1` (11h UTC = 8h Brasília, toda segunda) → `cli.py report-semanal`.
- `fechamento-mensal` — `0 11 1 * *` (todo dia 1) → `cli.py fechamento-mensal`.
- `checkin-diario` — `0 11 * * 1-5` (dias úteis) → `cli.py checkin-diario`.

O cron do Railway é em UTC e **não executa o comando no momento do deploy** (verificado) — só no horário agendado. `SLACK_BOT_TOKEN` fica como variável do serviço `checkin-diario`; os outros dois a referenciam (`${{checkin-diario.SLACK_BOT_TOKEN}}`). Para trocar comando/cron/variável de um serviço já criado é preciso um novo deploy (`serviceInstanceDeployV2`), não só "redeploy".

Os workflows de `.github/workflows/` (`weekly-report.yml`, `fechamento-mensal.yml`, `checkin-diario.yml`) **não têm mais `schedule`** — ficaram só com `workflow_dispatch`, como disparo manual de contingência (`gh workflow run …`). Se algum dia o Railway falhar, esse é o plano B; nunca reativar o `schedule` em paralelo (duplicaria a mensagem).

**"Hoje" dos jobs**: sempre calculado em `America/Sao_Paulo` (`zoneinfo`), nunca no relógio UTC do runner — evita datas erradas em qualquer teste manual fora do horário programado.

**Formato**: Slack Block Kit, mesmo padrão do Weekly Sales Report.

---

## 4. Mapeamento pessoa → Slack User ID

Reaproveita o mesmo mapeamento de `spec-weekly-sales-report.md` (seção 3), acrescido do Vinicius:

| Nome | Slack User ID |
|---|---|
| Vinicius (Vini) | `U09TK78CA1G` |
| Raolho (Lucas Pedroso) | `U021RCUQ02C` |
| Igor (Igor Ramos) | `U0BP9R96RRA` |
| Xande | `U02ELHA43QR` |
| Seixas (Lucas Seixas) | `U017XSY8S5U` |

Pessoa fora dessa lista (ex: nome novo aparecendo em "Agendada por"): exibir como texto puro, sem menção, e logar `WARNING` — mesmo comportamento do Weekly Sales Report.

**Dono do painel / alertas operacionais** (fora do mapeamento de pessoas acima): `U02ELHA43QR` também é o destinatário de DM para os alertas de falha de job descritos em §9 — coincide com o ID do Xande na tabela acima, mas são usos independentes (um é "quem agendou a call", o outro é "quem recebe alerta operacional").

---

## 5. Weekly Report — Estrutura

```
@channel
📊 Pré-vendas — Weekly Report
📅 {data de disparo, DD de Mês de AAAA}

🎯 Meta do mês (pré-vendas)
{n_realizadas} realizada(s) de {meta} (MTD: {mtd}) — {emoji} {pct}%
{barra de 10 blocos: 🟩/🟨/🟥 preenchido proporcional a realizadas/meta + ⬜ vazio, cor = mesmo status do badge}

📊 Projeção do mês (pré-vendas)
{n_agendadas} agendadas ({n_realizadas} realizada(s) + {n_a_realizar} a realizar)
⏰ Faltam {n_faltantes} call(s) e restam {n_dias_uteis} dia(s) úteis
   (ou, se a meta já estiver coberta: "⏰ Meta coberta pelo agendado")

📈 Total de agendamentos do mês (canais próprios + externos)
{n_total} no total — {n_realizados} realizados · {n_no_shows} no-shows · +{n_a_realizar} a realizar

🚫 No-show (meta = 10%)
Geral: {taxa_geral}% ({n} de {total}){🔴 se > 10%}
Pré-vendas: {taxa_pv}% ({n} de {total}){🔴 se > 10%}

📅 Agendamentos da semana
{n} calls programadas
- {data} · {empresa} · Agendada por: <@slack_id>
- ... (todas as calls da semana, ordenado por data — sem cap)

🔗 <link do painel|Clique aqui para acessar o painel completo →>
[divider real do Block Kit]
*Atenção:* reajam com um check ✅ quando virem esse report. Dúvidas, discussões e reports de bug aqui na thread 🧵
```

Observações sobre o template acima:
- **"realizada(s)", "call(s)", "dia(s)"**: sempre concordância gramatical real (1 realizada / 2 realizadas), nunca o literal "(s)".
- **Meta**: `{meta}` vem de config (`config/taxonomia.json` → `meta_mensal`, hoje = 20) — nunca escrita como número literal fixo no código, mesmo valendo 20 hoje.
- **Barra de progresso**: Slack Block Kit não tem barra nativa — decidido usar 10 blocos de emoji colorido (🟩 verde / 🟨 âmbar / 🟥 vermelho, conforme o status) + ⬜ pro restante, largura proporcional a `realizadas ÷ meta`.
- **Emoji de status inline**: tanto a linha de "Meta do mês" quanto a de "Resultado final" (Fechamento, §6) sempre trazem o emoji de status (🟢/🟡/🔴) colado antes do `%` — não só a cor da barra.
- **Alerta de no-show 🔴**: aparece **inline, por linha** (Geral e Pré-vendas avaliados independentemente — mesma regra de threshold único do painel), não como uma linha-selo separada embaixo das duas.
- **Agendamentos da semana**: **sem cap** — lista todas as calls da semana corrente, por menor ou maior que seja a lista (a v1 desta spec previa cap de 10 + "+N outras no painel"; removido a pedido, decisão mantida em 2026-09-04).
- **Link do painel**: sempre no formato clicável do Slack `<url|texto>`, texto fixo "Clique aqui para acessar o painel completo →" — nunca a URL crua no texto.
- **Rodapé de aviso**: depois do link do painel, um **divider real do Block Kit** (`{"type": "divider"}`, elemento nativo — não texto simulando linha com travessões) seguido de um bloco de texto: "*Atenção:* reajam com um check ✅ quando virem esse report. Dúvidas, discussões e reports de bug aqui na thread 🧵" — só "Atenção:" em negrito (`*Atenção:*`), o resto normal. Ordem final: link do painel → divider → aviso.

### Fonte de dados por seção (Weekly)

| Seção | Origem no JSON / regra |
|---|---|
| 🎯 Meta do mês | Hero metric do painel: **agendado pelo Vinicius, qualquer origem** (própria ou externa — mesma definição do hero do painel, `CLAUDE.md` seção 4; **não** exige canal próprio), filtrado para status "realizada". `MTD` calculado pelos **dias úteis** decorridos do mês (feriados incluídos) — cutoff = último dia útil completo antes de hoje, nunca dias corridos. `%` = realizadas ÷ MTD — mesmos thresholds de cor do painel (>90/70-90/<70) |
| 📊 Projeção do mês (pré-vendas) | Mesmo recorte do hero metric acima, mas contando todos os status (realizada + a realizar), não só realizada. "Faltam N calls" = meta − total agendado nesse recorte (nunca negativo). Dias úteis restantes = dias úteis totais do mês − dias úteis decorridos (mesmo cálculo do MTD, dias úteis — não corridos) |
| 📈 Total de agendamentos do mês | Todos os registros do mês, todos os canais (próprio + externo/Associados), sem filtro de quem agendou. Quebra por status: realizada / no-show / a realizar |
| 🚫 No-show | "Geral" = no-shows ÷ total **já realizado** (realizada + no-show, todos os canais — exclui "a realizar" do denominador). "Pré-vendas" = no-shows ÷ total já realizado dentro do recorte do hero (agendado pelo Vinicius, qualquer origem). Alerta 🔴 por linha, só se aquela linha ultrapassar 10% — mesma regra do painel (threshold único, sem faixa intermediária) |
| 📅 Agendamentos da semana | Calls com data dentro da semana corrente (da data de disparo até 6 dias depois — segunda a domingo, já que o disparo real é sempre segunda), qualquer status, qualquer canal. Sem cap — lista completa |

---

## 6. Fechamento Mensal — Estrutura

```
@channel
📊 Pré-vendas — Fechamento de {Mês}/{Ano}

🎯 Resultado final (pré-vendas): {N}/{meta} reuniões realizadas — {emoji} {pct}%
{mesma barra de 10 blocos do Weekly, escala 0–meta}

📈 Total de agendamentos (canais próprios + externos)
{n} no total — {n} realizados · {n} no-shows

🚫 No-show do mês (meta = 10%)
Geral: {taxa}% ({n} de {total}){🔴 se > 10%}
Pré-vendas: {taxa}% ({n} de {total}){🔴 se > 10%}

🔗 <link do painel|Clique aqui para acessar o painel completo →>
[divider real do Block Kit]
*Atenção:* reajam com um check ✅ quando virem esse report. Dúvidas, discussões e reports de bug aqui na thread 🧵
```

- **Header**: `{Mês}/{Ano}` por extenso (ex: "Agosto/2026") — não só o nome do mês.
- **Emoji do header**: **📊** (não 📆).
- **Rodapé de aviso**: mesmo bloco do Weekly — divider real do Block Kit + "*Atenção:* ..." (ver §5).

### Fonte de dados por seção (Fechamento Mensal)

| Seção | Origem no JSON / regra |
|---|---|
| 🎯 Resultado final (pré-vendas) | Hero metric do mês fechado — **agendado pelo Vinicius, qualquer origem** (mesma definição do hero do painel, §5 acima), só status "realizada" — número final, sem MTD (mês já fechado, não faz sentido comparar contra ritmo esperado) |
| 📈 Total de agendamentos | Todos os canais, todos os registros do mês fechado. Sem "a realizar" — mês fechado não tem pendência |
| 🚫 No-show do mês | Mesmo cálculo do Weekly (Geral vs. Pré-vendas, denominador = total já realizado), mas sobre o mês inteiro fechado, não a semana |

### Regras específicas do Fechamento Mensal

- **Trigger**: dia 1 do mês seguinte, data corrida (não precisa ser dia útil). Reporta o mês imediatamente anterior à data de disparo.
- **Menções**: só `@channel` no topo — sem menção individual a pessoas, diferente do Weekly.
- **Sem seção "Agendamentos da semana"** nem qualquer detalhamento por call individual — o Fechamento Mensal é só o placar, o detalhe fica no painel/Histórico.
- **Sem seção "Projeção"** — mês fechado não tem projeção, só resultado.

---

## 7. Regras de formatação (comuns aos dois reports)

- **MTD**: termo usado exclusivamente como "MTD" — nunca "esperado" ou "ritmo", mesma regra travada no painel (`CLAUDE.md`). Calculado por **dias úteis** (feriados incluídos), nunca dias corridos.
- **Cores de threshold**: sempre as mesmas do painel — hero badge >90% verde / 70-90% âmbar / <70% vermelho; no-show só vermelho acima de 10%, sem faixa intermediária.
- **No-show, denominador**: sempre "total já realizado" (realizada + no-show) — nunca "total agendado" (que incluiria "a realizar").
- **Meta mensal**: sempre lida de config (`meta_mensal`), nunca hardcoded como número literal no texto do report, mesmo o valor atual sendo 20.
- **Menções via `<@SLACK_ID>`** — nunca `@Nome` em texto puro (não dispara notificação).
- **Link do painel**: sempre `<url|texto>` (formato clicável do Slack), nunca a URL crua no texto — texto fixo "Clique aqui para acessar o painel completo →".
- **Concordância singular/plural real** (realizada/realizadas, call/calls, dia/dias) — nunca o literal "(s)".
- **Métrica de pré-vendas**: em toda a spec, "agendado pela pré-vendas" = agendado pelo Vinicius, **qualquer origem** (própria ou externa) — a mesma definição do hero do painel (`CLAUDE.md` seção 4). Não exige canal próprio.
- **Emojis fixos por seção**, mesmo padrão do Weekly Sales Report, pra manter reconhecimento visual: 🎯 📊 📈 🚫 📅 🔗 (Weekly) / 🎯 📊 📈 🚫 🔗 (Fechamento Mensal).
- **Rodapé de engajamento**: mesma regra dos reports de Vendas — toda mensagem termina com um **divider real do Block Kit** seguido de um bloco de texto pedindo reação de confirmação de leitura (✅) e direcionando dúvidas/bugs pra thread (🧵), com "*Atenção:*" em negrito e o resto normal.
- **Mês fechado**: a checagem "o mês fechou desde o último Weekly?" **não é necessária** no Weekly Report — como o Fechamento Mensal é um job separado (dia 1, independente de dia da semana), o Weekly de segunda sempre reporta o mês corrente em andamento, mesmo que tenha acabado de virar (pré-vendas já projeta o mês seguinte antes dele começar, então nunca há um "mês zerado" de fato).

---

## 8. Fora de escopo (v1)

- Detecção automática de mês fechado dentro do Weekly — resolvido via job separado (Fechamento Mensal), não via condicional no Weekly.
- Menção individual no Fechamento Mensal — decisão explícita de manter só `@channel`.
- Seção "Por canal" / "Por pessoa" no Fechamento Mensal — mantido enxuto, esse detalhamento já existe no painel (Histórico).
- Detecção automática de mensagens indevidas no canal errado — a remoção (`apagar-mensagem`) é sempre disparada manualmente, nunca automática.

---

## 9. Decisões de implementação e histórico de correções (2026-09-03/04)

Pontos que a v1 desta spec deixava em aberto ou registrava errado, decididos/corrigidos durante e depois da implementação:

- **Correção de canal (2026-09-04)**: a v1 listava `C09TLCZB88M` (canal de **vendas**, o mesmo do Weekly Sales Report) — valor errado, só percebido no primeiro disparo real de produção (Fechamento de Agosto/2026), que saiu no canal errado por engano. O valor correto e definitivo é `C09UJ55HQHW` (canal dedicado de Pré-vendas) — já é o que está em `config/slack_reports.json`. A mensagem indevida no canal de vendas ficou pendente de remoção manual (ver pendência abaixo).
- **MTD e dias úteis restantes**: sempre por dias úteis (com feriados), nunca dias corridos — a v1 descrevia "pro-rata pelos dias corridos", divergente do que o painel já fazia e do que `src/calc.py` implementa.
- **No-show, denominador**: sempre "total já realizado" (realizada + no-show), nunca "total agendado" (que incluiria "a realizar") — a v1 usava a fórmula errada nas duas linhas (Geral e Pré-vendas).
- **Agendamentos da semana sem cap**: a v1 previa cap de 10 + "+N outras no painel"; removido a pedido — lista a semana inteira, do tamanho que for.
- **Hosting do cron**: começou em GitHub Actions (2026-09) e **migrou pro Railway em 2026-10-07** (ver §3). Motivo: o cron do GitHub é "melhor esforço" e, a partir de 05/10, o Check Diário passou a atrasar 6–8h (05/10 às 16h24, 06/10 às 13h58 BRT) ou a não disparar no dia — o GitHub não reportava incidente e o workflow/secret estavam corretos (o `workflow_dispatch` manual rodava na hora). O Railway exigiu plano pago (Hobby): o trial expirou e o Free não comporta o projeto de Vendas + o novo.
- **Timezone dos jobs**: "hoje" sempre calculado em `America/Sao_Paulo` via `zoneinfo`, nunca no UTC do runner — não estava na v1.
- **Módulo de cálculo compartilhado**: `src/calc.py` (Python), porta a lógica do painel (que roda em JS no navegador) — ver §2. A v1 tratava isso como próximo passo; já implementado.
- **Config dos jobs**: `config/slack_reports.json` (canal, dono, URL do painel, mapeamento pessoa→Slack ID) — a v1 tratava isso como próximo passo; já implementado.
- **Autenticação Slack**: Bot Token (`chat.postMessage`), guardado como variável `SLACK_BOT_TOKEN` no Railway (e ainda como secret no GitHub, usado só pelos workflows manuais de contingência). Bot: `jordan_belfort`.
- **Falha ao postar no canal**: até 3 tentativas com backoff exponencial (2s, 4s, 8s — `src/slack.py`). Se todas falharem, o job manda uma **DM pro dono do painel** (`U02ELHA43QR`, ver §4) com a mensagem de erro, além de logar no histórico de execuções do serviço no Railway.
- **Mês sem dado** (`data/{AAAA-MM}.json` não existe quando o job roda): o job **não posta nada no canal público** — em vez disso, manda DM pro dono avisando (`"⚠️ O {report} de Pré-vendas não saiu hoje — arquivo data/{mes}.json não existe."`), loga o erro e encerra com código de saída ≠ 0 (fica visível como falha no histórico de execuções).
- **Rodapé de aviso (divider + "Atenção")**: o `───────────` usado nas versões anteriores desta spec pra representar o rodapé era só uma representação visual do documento — o elemento real é sempre um `divider` do Block Kit (`{"type": "divider"}`), não texto com travessões. Confirmado como já implementado em `src/reports.py`, ordem final: link do painel → divider → "*Atenção:* ...".
- **CLI** (no repositório do painel, `cli.py`):
  - `report-semanal [--mes YYYY-MM] [--dry-run]`
  - `fechamento-mensal [--mes YYYY-MM] [--dry-run]`
  - `checkin-diario [--mes YYYY-MM] [--dry-run]` — DM diária pro Vinicius (§11). Reaproveita o fluxo de `_run_report`, com destino sobrescrito pro Slack ID dele.
  - `test-slack` — valida o token (`auth.test`) e manda uma DM de teste pro dono, sem tocar no canal público. Usado pra validar a configuração do secret sem risco de poluir o canal real. Não estava na v1.
  - `apagar-mensagem --canal ID --contem "texto"` — utilitário de manutenção pra apagar uma mensagem indevida do bot (ex: post que foi pro canal errado, ver correção de canal acima). Não estava na v1. **Pendência conhecida**: precisa do escopo `channels:history` (ou `groups:history` se o canal for privado) no Slack App, que ainda não tinha sido concedido na primeira vez que foi usado — reinstalação do app pendente, sem ação agendada ainda.
  - `--dry-run` em `report-semanal`/`fechamento-mensal`: imprime o payload Block Kit (JSON) em vez de postar — usado pra validar visualmente o formato antes de considerar uma mudança aplicada.
  - Todos os comandos leem `config/slack_reports.json` (canal, dono, URL do painel, mapeamento pessoa→Slack ID).

---

## 10. Próximos passos

1. ~~Implementar os dois jobs (cron semanal segunda 8h + cron mensal dia 1), lendo do JSON stateful do painel de pré-vendas.~~ **Feito** — GitHub Actions (2026-09) e depois Railway (2026-10-07), ver §3.
2. ~~Extrair a lógica de cálculo (hero metric, MTD, thresholds, taxa de no-show) para módulo compartilhado entre painel e reports, evitando duplicar regra em dois lugares.~~ **Feito** — `src/calc.py` (§2 e §9).
3. ~~Adicionar o mapeamento pessoa → Slack ID (§4) como config dos jobs.~~ **Feito** — `config/slack_reports.json`.
4. Validar manualmente as primeiras execuções de cada report antes de considerar produção estável. **Em andamento**: Fechamento Mensal de agosto/2026 já rodou de verdade em produção (após corrigir o canal, §3/§9); Weekly Report ainda não teve um disparo real de segunda-feira (próximo: 07/09/2026).
5. **Acompanhar os primeiros disparos reais no Railway**: Check Diário (primeiro: 08/10/2026), Weekly (12/10) e Fechamento Mensal (01/11). Nenhum agendamento do Railway foi exercitado ainda — só `--dry-run` e `test-slack` manuais.
6. Conceder ao Slack App o escopo `channels:history`/`groups:history` e reinstalar, pra destravar o utilitário `apagar-mensagem` (usado pra limpar a mensagem que foi parar no canal de vendas por engano) — pendência conhecida, sem prazo definido.

---

## 11. Check Diário (DM do Vinicius)

Criado em 2026-10-07. O Vinicius confirma cada call com o lead pra evitar no-show; o bot manda a lista do dia direto na DM dele pra ele não precisar abrir a agenda. **DM, não canal** — destino = Slack ID dele (`pessoa_slack_id[presales_agendador]`, `U09TK78CA1G`). Sem `@channel`, sem rodapé de engajamento (isso é regra dos reports de canal).

**Disparo**: dias úteis, 8h Brasília (Railway, §3). Não há tratamento de feriado: num feriado ele recebe a mensagem de "sem calls" ou a lista normal, conforme os dados.

**Conteúdo** — calls com `data = hoje`, agendadas por Vinicius Almeida (mesma definição de pré-vendas do hero), status efetivo `a_realizar` (call já marcada como no-show/realizada no dia não entra), ordenadas por empresa (a hora não é guardada, §8 do CLAUDE.md, então não há ordem por horário). Uma única section do Block Kit:

```
👋 Fala Vini! Essas são as calls de hoje (DD/MM) que precisam da sua confirmação de agenda com o lead:

1. Empresa A
2. Empresa B
```

Sem nenhuma call, a mensagem muda (e é enviada mesmo assim, pra ele saber que o bot rodou):

```
👋 Fala Vini! Não tem nenhuma call prevista pra acontecer hoje (DD/MM) e que foi agendada por você... Vale a pena você dar um check em como está a sua performance em relação a meta do mês. Bora pra cima!
```

**Limites conhecidos**: só nome da empresa — sem horário, contato ou telefone (nenhum é persistido; `data/*.json` é público, ver CLAUDE.md §8/§13). Quem confirma ainda abre o Pipedrive pra falar com o lead. Calls marcadas depois das 8h não entram naquele dia.

**Falha**: mesmas regras do restante (§9) — até 3 tentativas, DM de erro pro dono; arquivo do mês inexistente → DM de aviso pro dono, nada pro Vinicius.
