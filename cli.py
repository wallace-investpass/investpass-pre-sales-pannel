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

Exemplos:
  python3 cli.py import calls.txt --mes 2026-09
  echo "Empresa — 10/09 — CONARH — WhatsApp (Agendada por @Vinicius Almeida)" | python3 cli.py import - --mes 2026-09
  python3 cli.py no-show "Empresa" --mes 2026-09
  python3 cli.py mudar-data "Empresa" --mes 2026-09 --nova-data 15/09
  python3 cli.py gerar --mes 2026-09 --push
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import parser as call_parser
from src import store
from src import metrics as metrics_mod
from src import dashboard as dashboard_mod
from src import taxonomy as tax

REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"


def current_mes():
    hoje = datetime.date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"


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
        _git_publish(payload["defaultMes"])


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

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
