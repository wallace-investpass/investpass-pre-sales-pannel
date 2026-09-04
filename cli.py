#!/usr/bin/env python3
"""CLI do painel de pré-vendas investPass.

Comandos:
  import <arquivo|-> [--mes YYYY-MM] [--ano YYYY]
      Lê o arquivo (ou stdin, se "-") e adiciona todas as calls encontradas
      (formato compacto, uma por linha, ou mensagem(ns) do Slack) à lista mestra.
      Também serve para adicionar uma única call — não há distinção de comando.

  no-show <empresa> --mes YYYY-MM [--data DD/MM]
      Marca uma call como no-show (status vira 'realizada', noShow=true).
      Desambiguação por empresa + --data quando há mais de uma call.

  mudar-data <empresa> --mes YYYY-MM --nova-data DD/MM [--data-atual DD/MM] [--ano YYYY]
      Atualiza a data de uma call. Se a nova data cair em outro mês, a call é
      movida para a lista mestra desse mês.

  gerar [--mes YYYY-MM] [--push]
      Embute os dados brutos de TODOS os meses salvos num único
      docs/index.html (abas Detalhe mensal/Histórico, dropdown de mês) —
      esse é o arquivo servido pelo GitHub Pages. A transição a_realizar→
      realizada, MTD e todas as métricas dependentes de data são calculadas
      no navegador, ao vivo, com o relógio de quem está olhando a página —
      não são calculadas nem persistidas aqui (seção 9 do CLAUDE.md).
      --mes só escolhe qual mês abre selecionado por padrão (default: o
      mais recente salvo). --push também faz commit + push de docs/
      automaticamente, publicando a atualização (seção 13 do CLAUDE.md).

  report-semanal [--mes YYYY-MM] [--dry-run]
      Publica o Weekly Report de pré-vendas no canal do Slack (spec-
      prevendas-reports.md). Roda via GitHub Actions toda segunda 8h
      (horário de Brasília). --mes força o mês reportado (default: mês
      corrente). --dry-run imprime o payload Block Kit em vez de postar.
      Exige a env var SLACK_BOT_TOKEN.

  fechamento-mensal [--mes YYYY-MM] [--dry-run]
      Publica o Fechamento Mensal de pré-vendas no canal do Slack. Roda via
      GitHub Actions todo dia 1, 8h (horário de Brasília). --mes força o
      mês reportado (default: mês anterior ao corrente). Exige a env var
      SLACK_BOT_TOKEN.

  test-slack
      Valida SLACK_BOT_TOKEN (auth.test) e manda uma DM de teste pro dono
      do painel — não posta no canal público. Uso manual/dev.

  apagar-mensagem --canal ID --contem "texto" [--limite N]
      Apaga a mensagem mais recente do bot num canal/DM cujo texto contenha
      "texto" — utilitário de manutenção pra corrigir posts indo pro canal
      errado. Uso manual/dev.

Exemplos:
  python3 cli.py import calls.txt --mes 2026-09
  echo "Empresa — 10/09 — CONARH — WhatsApp (Agendada por @Vinicius Almeida)" | python3 cli.py import - --mes 2026-09
  python3 cli.py no-show "Empresa" --mes 2026-09
  python3 cli.py mudar-data "Empresa" --mes 2026-09 --nova-data 15/09
  python3 cli.py gerar --mes 2026-09 --push
"""
import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import parser as call_parser
from src import store
from src import metrics as metrics_mod
from src import dashboard as dashboard_mod
from src import taxonomy as tax
from src import calc as calc_mod
from src import reports as reports_mod
from src import slack as slack_mod

REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"
BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def current_mes():
    hoje = datetime.date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"


def hoje_brasilia():
    """'Hoje' dos jobs de report é o relógio de Brasília, não o do runner do
    cron (que roda em UTC) — spec-prevendas-reports.md, seção 3."""
    return datetime.datetime.now(BRASILIA_TZ).date()


def mes_anterior(hoje):
    primeiro_dia_atual = hoje.replace(day=1)
    ultimo_dia_anterior = primeiro_dia_atual - datetime.timedelta(days=1)
    return f"{ultimo_dia_anterior.year:04d}-{ultimo_dia_anterior.month:02d}"


def _slack_token():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("erro: variável de ambiente SLACK_BOT_TOKEN não configurada.")
        sys.exit(1)
    return token


def cmd_import(args):
    mes = args.mes or current_mes()
    ano = args.ano or int(mes.split("-")[0])
    texto = sys.stdin.read() if args.arquivo == "-" else Path(args.arquivo).read_text(encoding="utf-8")

    taxonomia = tax.load_taxonomia()
    calls, errors = call_parser.parse_bulk(texto, ano=ano, taxonomia=taxonomia)

    if not calls and not errors:
        print("nada para importar.")
        return

    resultados = store.add_calls_bulk(mes, calls)
    total_avisos = 0
    for call, warnings in resultados:
        print(f"+ {call['empresa']} ({call['data']}) — {call['origem']} / {call['canal']} — status={call['status']}")
        for w in warnings:
            print(f"  ! {w}")
            total_avisos += 1

    if errors:
        print(f"\n{len(errors)} linha(s)/bloco(s) não reconhecido(s):")
        for tipo, trecho in errors:
            print(f"  [{tipo}] {trecho}")

    print(f"\n{len(calls)} call(s) adicionada(s) a {mes}, {total_avisos} aviso(s), {len(errors)} erro(s) de parsing.")


def cmd_no_show(args):
    mes = args.mes or current_mes()
    call, erro = store.mark_no_show(mes, args.empresa, data=_ddmm_para_iso(args.data, mes))
    if erro:
        print(f"erro: {erro}")
        sys.exit(1)
    print(f"no-show marcado: {call['empresa']} ({call['data']})")


def cmd_mudar_data(args):
    mes = args.mes or current_mes()
    ano = args.ano or int(mes.split("-")[0])
    call, novo_mes, erro = store.change_date(
        mes, args.empresa, args.nova_data, ano=ano,
        data_atual=_ddmm_para_iso(args.data_atual, mes),
    )
    if erro:
        print(f"erro: {erro}")
        sys.exit(1)
    if novo_mes != mes:
        print(f"data alterada: {call['empresa']} → {call['data']} (movida de {mes} para {novo_mes})")
    else:
        print(f"data alterada: {call['empresa']} → {call['data']}")


def _ddmm_para_iso(ddmm, mes):
    if not ddmm:
        return None
    ano = int(mes.split("-")[0])
    dia, m = ddmm.split("/")
    return f"{ano:04d}-{int(m):02d}-{int(dia):02d}"


def cmd_gerar(args):
    meses = store.list_months()
    if not meses:
        print("nenhum mês salvo em data/ ainda — importe calls antes de gerar o dashboard.")
        return

    months_data = [(mes, store.load_month(mes)) for mes in meses]

    taxonomia = tax.load_taxonomia()
    feriados = tax.load_feriados()
    payload = metrics_mod.compute_all_months(months_data, taxonomia, feriados)

    if args.mes and args.mes in payload["months"]:
        payload["defaultMes"] = args.mes

    generated_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    html_out = dashboard_mod.render(payload, generated_at=generated_at)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / "index.html"
    out_path.write_text(html_out, encoding="utf-8")

    print(f"dashboard gerado: {out_path}")
    print("(aberto/fechado e as métricas de cada mês são calculados ao vivo no navegador, com o relógio de quem está olhando — não aparecem aqui.)")
    for mes in meses:
        m = payload["months"][mes]
        n_real = sum(1 for c in m["calls"] if c["status"] == "realizada")
        n_ar = sum(1 for c in m["calls"] if c["status"] == "a_realizar")
        print(f"  {mes}: {len(m['calls'])} call(s) salva(s) ({n_real} realizada(s), {n_ar} a_realizar salva(s) — meta {m['meta']})")

    if args.push:
        _git_publish(payload["defaultMes"] or meses[-1])


def _git_publish(mes_atual):
    def run(*cmd):
        return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)

    add = run("git", "add", "docs")
    if add.returncode != 0:
        print(f"git add falhou: {add.stderr.strip()}")
        return

    diff = run("git", "diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("nada novo pra publicar (dashboard idêntico ao último commit).")
        return

    msg = f"Atualiza painel — {mes_atual} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
    commit = run("git", "commit", "-m", msg)
    if commit.returncode != 0:
        print(f"git commit falhou: {commit.stderr.strip()}")
        return

    push = run("git", "push")
    if push.returncode != 0:
        print(f"git push falhou: {push.stderr.strip()}")
        return

    print("publicado no GitHub Pages (commit + push feitos).")


def _run_report(mes, hoje, builder_fn, tipo_label, args):
    """Fluxo comum aos dois reports de Slack (decidido em 2026-09-03, fora
    da spec original):
    - Se data/{mes}.json não existir: não posta no canal, manda DM de aviso
      pro dono e loga o erro.
    - Se o post no canal falhar (mesmo após retry com backoff, ver
      src/slack.py): manda DM de erro pro dono e loga.
    """
    slack_cfg = tax.load_slack_reports_config()
    token = None if args.dry_run else _slack_token()

    if not store.month_file(mes).exists():
        msg = f"⚠️ O {tipo_label} de Pré-vendas não saiu hoje — arquivo data/{mes}.json não existe."
        print(f"erro: {msg}")
        if args.dry_run:
            print("(dry-run: DM de aviso não enviada)")
        else:
            slack_mod.notify_owner(token, slack_cfg["owner_user_id"], msg)
        sys.exit(1)

    state = store.load_month(mes)
    taxonomia = tax.load_taxonomia()
    feriados = set(tax.load_feriados())

    blocks, fallback = builder_fn(mes, state, taxonomia, feriados, hoje, slack_cfg)

    if args.dry_run:
        import json as _json
        print(_json.dumps(blocks, ensure_ascii=False, indent=2))
        print(f"\n(fallback text: {fallback})")
        return

    try:
        slack_mod.post_message(token, slack_cfg["channel_id"], fallback, blocks=blocks)
        print(f"{tipo_label} publicado no canal {slack_cfg['channel_id']}.")
    except slack_mod.SlackError as e:
        erro_msg = f"❌ O {tipo_label} de Pré-vendas falhou ao publicar no canal: {e}"
        print(f"erro: {erro_msg}")
        slack_mod.notify_owner(token, slack_cfg["owner_user_id"], erro_msg)
        sys.exit(1)


def cmd_report_semanal(args):
    hoje = hoje_brasilia()
    mes = args.mes or f"{hoje.year:04d}-{hoje.month:02d}"
    _run_report(mes, hoje, reports_mod.build_weekly_report, "Weekly Report", args)


def cmd_fechamento_mensal(args):
    hoje = hoje_brasilia()
    mes = args.mes or mes_anterior(hoje)
    _run_report(mes, hoje, reports_mod.build_fechamento_mensal, "Fechamento Mensal", args)


def cmd_test_slack(args):
    """Valida que SLACK_BOT_TOKEN está configurado e que o bot consegue
    autenticar e mandar DM — sem tocar no canal público de reports."""
    token = _slack_token()
    slack_cfg = tax.load_slack_reports_config()

    try:
        info = slack_mod.auth_test(token)
    except slack_mod.SlackError as e:
        print(f"erro: auth.test falhou — token inválido ou sem permissão: {e}")
        sys.exit(1)

    print(f"auth.test ok: team={info.get('team')} user={info.get('user')} bot_id={info.get('bot_id')}")

    owner = slack_cfg["owner_user_id"]
    try:
        slack_mod.post_message(
            token, owner,
            f"✅ Teste de conexão do bot de reports de pré-vendas — tudo certo (workspace: {info.get('team')}).",
            retries=1,
        )
    except slack_mod.SlackError as e:
        print(f"erro: consegui autenticar, mas a DM pro dono ({owner}) falhou: {e}")
        sys.exit(1)

    print(f"DM de teste enviada com sucesso para {owner}.")


def cmd_apagar_mensagem(args):
    """Utilitário de manutenção: acha a mensagem mais recente do bot num
    canal cujo texto contenha --contem, e apaga. Usado pra corrigir posts
    que foram parar no canal errado (ex: config errada de channel_id)."""
    token = _slack_token()
    try:
        info = slack_mod.auth_test(token)
        mensagens = slack_mod.list_recent_messages(token, args.canal, limit=args.limite)
    except slack_mod.SlackError as e:
        print(f"erro: {e}")
        sys.exit(1)

    bot_id = info.get("bot_id")
    candidatas = [
        m for m in mensagens
        if m.get("bot_id") == bot_id and args.contem in m.get("text", "")
    ]
    if not candidatas:
        print(f"nenhuma mensagem do bot encontrada em {args.canal} contendo '{args.contem}'.")
        sys.exit(1)

    alvo = candidatas[0]
    print(f"apagando mensagem ts={alvo['ts']} em {args.canal}:")
    print(f"  {alvo.get('text', '')[:200]}")
    try:
        slack_mod.delete_message(token, args.canal, alvo["ts"])
    except slack_mod.SlackError as e:
        print(f"erro ao apagar: {e}")
        sys.exit(1)
    print("mensagem apagada com sucesso.")


def main():
    p = argparse.ArgumentParser(description="Painel de pré-vendas investPass")
    sub = p.add_subparsers(dest="comando", required=True)

    p_import = sub.add_parser("import", help="importa uma ou mais calls de um arquivo (ou stdin com '-')")
    p_import.add_argument("arquivo")
    p_import.add_argument("--mes", help="YYYY-MM (default: mês atual)")
    p_import.add_argument("--ano", type=int, help="ano para datas DD/MM sem ano explícito (default: ano do --mes)")
    p_import.set_defaults(func=cmd_import)

    p_ns = sub.add_parser("no-show", help="marca uma call como no-show")
    p_ns.add_argument("empresa")
    p_ns.add_argument("--mes", help="YYYY-MM (default: mês atual)")
    p_ns.add_argument("--data", help="DD/MM, para desambiguar se a empresa tiver mais de uma call")
    p_ns.set_defaults(func=cmd_no_show)

    p_md = sub.add_parser("mudar-data", help="muda a data de uma call")
    p_md.add_argument("empresa")
    p_md.add_argument("--mes", help="YYYY-MM (default: mês atual)")
    p_md.add_argument("--nova-data", required=True, help="DD/MM")
    p_md.add_argument("--data-atual", help="DD/MM, para desambiguar se a empresa tiver mais de uma call")
    p_md.add_argument("--ano", type=int, help="ano da nova data (default: ano do --mes)")
    p_md.set_defaults(func=cmd_mudar_data)

    p_gerar = sub.add_parser("gerar", help="gera o dashboard HTML (todos os meses, num único arquivo)")
    p_gerar.add_argument("--mes", help="YYYY-MM que abre selecionado por padrão (default: mês mais recente salvo)")
    p_gerar.add_argument("--push", action="store_true", help="commit + push automático de docs/ (publica no GitHub Pages)")
    p_gerar.set_defaults(func=cmd_gerar)

    p_semanal = sub.add_parser("report-semanal", help="gera e publica o Weekly Report de pré-vendas no Slack")
    p_semanal.add_argument("--mes", help="YYYY-MM (default: mês corrente, horário de Brasília)")
    p_semanal.add_argument("--dry-run", action="store_true", help="imprime o payload Block Kit em vez de postar no Slack")
    p_semanal.set_defaults(func=cmd_report_semanal)

    p_fechamento = sub.add_parser("fechamento-mensal", help="gera e publica o Fechamento Mensal de pré-vendas no Slack")
    p_fechamento.add_argument("--mes", help="YYYY-MM (default: mês anterior ao corrente, horário de Brasília)")
    p_fechamento.add_argument("--dry-run", action="store_true", help="imprime o payload Block Kit em vez de postar no Slack")
    p_fechamento.set_defaults(func=cmd_fechamento_mensal)

    p_test_slack = sub.add_parser("test-slack", help="valida SLACK_BOT_TOKEN (auth.test + DM de teste pro dono, sem tocar no canal público)")
    p_test_slack.set_defaults(func=cmd_test_slack)

    p_apagar = sub.add_parser("apagar-mensagem", help="apaga a mensagem mais recente do bot num canal contendo um texto (manutenção/correção de erro)")
    p_apagar.add_argument("--canal", required=True, help="ID do canal/DM onde procurar")
    p_apagar.add_argument("--contem", required=True, help="trecho de texto que a mensagem a apagar deve conter")
    p_apagar.add_argument("--limite", type=int, default=20, help="quantas mensagens recentes buscar (default: 20)")
    p_apagar.set_defaults(func=cmd_apagar_mensagem)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
