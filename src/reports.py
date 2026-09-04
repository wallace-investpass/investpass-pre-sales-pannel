"""Monta os payloads Block Kit dos dois reports de Slack (spec-prevendas-
reports.md): Weekly Report (toda segunda) e Fechamento Mensal (todo dia 1).
Usa src/calc.py para os números — nunca reimplementa MTD/thresholds/no-show
aqui (seção 2 da spec).
"""
import datetime

from . import calc
from .metrics import MESES_PT

BAR_LEN = 10
BAR_FILL_EMOJI = {"green": "🟩", "amber": "🟨", "red": "🟥"}
NS_LIMIT_PCT = 10


def mes_label(mes_key, sep=" "):
    ano, mes_num = (int(x) for x in mes_key.split("-"))
    return f"{MESES_PT[mes_num]}{sep}{ano}"


def data_disparo_label(hoje):
    return f"{hoje.day:02d} de {MESES_PT[hoje.month].lower()} de {hoje.year}"


def render_bar(ratio, css):
    ratio = max(0.0, min(1.0, ratio))
    filled = round(ratio * BAR_LEN)
    return BAR_FILL_EMOJI[css] * filled + "⬜" * (BAR_LEN - filled)


def mention_for(nome_completo, pessoa_slack_id):
    slack_id = pessoa_slack_id.get(nome_completo)
    if slack_id:
        return f"<@{slack_id}>"
    print(f"WARNING: pessoa '{nome_completo}' não mapeada para Slack ID (config/slack_reports.json) — exibindo texto puro")
    return nome_completo


def _ns_flag(pct):
    return " 🔴" if pct > NS_LIMIT_PCT else ""


def _section(text):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _divider():
    return {"type": "divider"}


def _painel_link_section(slack_cfg):
    """Seção final de link do painel, compartilhada pelos dois reports —
    usa o formato de link do Slack <url|texto> em vez da URL crua."""
    return _section(f"🔗 <{slack_cfg['painel_url']}|Clique aqui para acessar o painel completo →>")


def build_weekly_report(mes_key, state, taxonomia, feriados_set, hoje, slack_cfg):
    m = calc.month_metrics(mes_key, state, taxonomia, feriados_set, hoje)
    mtd = calc.compute_mtd(mes_key, hoje, feriados_set)
    meta = m["meta"]
    hero = m["presalesRealTotal"]
    hoje_iso = calc.iso_of(hoje)

    expected = mtd["pctMtd"] * meta
    ratio = (hero / expected) if expected > 0 else (1.0 if hero == 0 else 2.0)
    st = calc.status_of(ratio)
    pct_mtd = round(ratio * 100)
    bar = render_bar((hero / meta) if meta else 0, st["css"])

    n_agendadas = hero + m["presalesAr"]
    faltam = max(0, meta - n_agendadas)
    dias_restantes = mtd["diasUteisRestantes"]

    semana_fim_iso = calc.iso_of(hoje + datetime.timedelta(days=6))
    semana_calls = sorted(
        (c for c in state["calls"] if c.get("data") and hoje_iso <= c["data"] <= semana_fim_iso),
        key=lambda c: c["data"],
    )

    cap = 10
    pessoa_slack_id = slack_cfg["pessoa_slack_id"]
    linhas_semana = []
    for c in semana_calls[:cap]:
        dd, mm = c["data"][8:10], c["data"][5:7]
        mention = mention_for(c["agendadoPor"], pessoa_slack_id)
        linhas_semana.append(f"- {dd}/{mm} · {c['empresa']} · Agendada por: {mention}")
    if not linhas_semana:
        linhas_semana = ["_nenhuma call programada para esta semana_"]
    restantes = len(semana_calls) - cap
    if restantes > 0:
        linhas_semana.append(f"+ {restantes} outras no painel")

    header = f"📊 *Pré-vendas — Weekly Report*\n📅 {data_disparo_label(hoje)}"

    blocks = [
        _section(f"<!channel>\n{header}"),
        _divider(),
        _section(
            "*🎯 Meta do mês (pré-vendas)*\n"
            f"{hero} realizada(s) de {meta} (MTD: {round(expected)}) — {st['emoji']} {pct_mtd}%\n"
            f"{bar}"
        ),
        _section(
            "*📊 Projeção do mês (pré-vendas)*\n"
            f"{n_agendadas} agendadas ({hero} realizada(s) + {m['presalesAr']} a realizar)\n"
            + (
                f"⏰ Faltam {faltam} call{'s' if faltam != 1 else ''} e "
                f"restam {dias_restantes} dia{'s' if dias_restantes != 1 else ''} úteis"
                if faltam > 0
                else "⏰ Meta coberta pelo agendado"
            )
        ),
        _section(
            "*📈 Total de agendamentos do mês (canais próprios + externos)*\n"
            f"{m['totalGeral']} no total — {m['totalReal']} realizados · "
            f"{m['totalNs']} no-shows · +{m['totalAr']} a realizar"
        ),
        _section(
            "*🚫 No-show (meta = 10%)*\n"
            f"Geral: {m['nsTotalPct']}% ({m['totalNs']} de {m['totalReal'] + m['totalNs']}){_ns_flag(m['nsTotalPct'])}\n"
            f"Pré-vendas: {m['nsPvPct']}% ({m['presalesNsCount']} de {m['presalesRealizadasCount']}){_ns_flag(m['nsPvPct'])}"
        ),
        _section(f"*📅 Agendamentos da semana*\n{len(semana_calls)} calls programadas\n" + "\n".join(linhas_semana)),
        _divider(),
        _painel_link_section(slack_cfg),
    ]

    fallback = f"Pré-vendas Weekly Report — {hero} de {meta} realizadas ({pct_mtd}% do MTD)"
    return blocks, fallback


def build_fechamento_mensal(mes_key, state, taxonomia, feriados_set, hoje, slack_cfg):
    m = calc.month_metrics(mes_key, state, taxonomia, feriados_set, hoje)
    meta = m["meta"]
    hero = m["presalesRealTotal"]
    ratio = (hero / meta) if meta else (1.0 if hero == 0 else 2.0)
    st = calc.status_of(ratio)
    pct = round(ratio * 100)
    bar = render_bar((hero / meta) if meta else 0, st["css"])

    header = f"📊 *Pré-vendas — Fechamento de {mes_label(mes_key, sep='/')}*"

    blocks = [
        _section(f"<!channel>\n{header}"),
        _divider(),
        _section(
            f"*🎯 Resultado final (pré-vendas): {hero}/{meta} reuniões realizadas — {st['emoji']} {pct}%*\n{bar}"
        ),
        _section(
            "*📈 Total de agendamentos (canais próprios + externos)*\n"
            f"{m['totalReal'] + m['totalNs']} no total — {m['totalReal']} realizados · {m['totalNs']} no-shows"
        ),
        _section(
            "*🚫 No-show do mês (meta = 10%)*\n"
            f"Geral: {m['nsTotalPct']}% ({m['totalNs']} de {m['totalReal'] + m['totalNs']}){_ns_flag(m['nsTotalPct'])}\n"
            f"Pré-vendas: {m['nsPvPct']}% ({m['presalesNsCount']} de {m['presalesRealizadasCount']}){_ns_flag(m['nsPvPct'])}"
        ),
        _divider(),
        _painel_link_section(slack_cfg),
    ]

    fallback = f"Pré-vendas Fechamento de {mes_label(mes_key, sep='/')} — {hero}/{meta} ({pct}%)"
    return blocks, fallback
