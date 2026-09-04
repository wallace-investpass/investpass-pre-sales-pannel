"""Lógica de cálculo compartilhada entre o painel e os reports de Slack
(spec-prevendas-reports.md, seção 2: "não reimplementar essas regras em
paralelo"). O painel calcula tudo isso em JS, ao vivo, no navegador
(dashboard.py) porque depende do relógio de quem está olhando a página
(seção 4/9 do CLAUDE.md) — os reports rodam num cron (sem usuário olhando),
então esse módulo é a porta em Python da mesma regra, usada como fonte única
para os dois jobs (Weekly Report e Fechamento Mensal). Qualquer mudança de
regra de negócio (MTD, thresholds, no-show, meta) que afete o painel também
precisa ser replicada aqui.
"""
import calendar
import datetime


def parse_iso(iso):
    ano, mes, dia = (int(x) for x in iso.split("-"))
    return datetime.date(ano, mes, dia)


def iso_of(d):
    return d.isoformat()


def is_business_day(d, feriados_set):
    return d.weekday() < 5 and iso_of(d) not in feriados_set


def business_days(d1, d2, feriados_set):
    if d1 > d2:
        return 0
    n = 0
    d = d1
    one_day = datetime.timedelta(days=1)
    while d <= d2:
        if is_business_day(d, feriados_set):
            n += 1
        d += one_day
    return n


def mtd_cutoff_date(hoje, feriados_set):
    """Último dia útil completo anterior a hoje — nunca o próprio hoje
    (seção 4 do CLAUDE.md)."""
    d = hoje - datetime.timedelta(days=1)
    while not is_business_day(d, feriados_set):
        d -= datetime.timedelta(days=1)
    return d


def month_bounds(mes_key):
    ano, mes = (int(x) for x in mes_key.split("-"))
    inicio = datetime.date(ano, mes, 1)
    fim = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])
    return inicio, fim


def compute_mtd(mes_key, hoje, feriados_set):
    inicio, fim = month_bounds(mes_key)
    cutoff = mtd_cutoff_date(hoje, feriados_set)
    dias_uteis_total = business_days(inicio, fim, feriados_set)
    # Se o cutoff cair no mês anterior (início do mês, nenhum dia útil
    # completo decorrido ainda), decorridos é 0 — não força a data do
    # cutoff pro início do mês (seção 4 do CLAUDE.md).
    if cutoff < inicio:
        dias_uteis_decorridos = 0
    else:
        dias_uteis_decorridos = business_days(inicio, min(cutoff, fim), feriados_set)
    return {
        "cutoff": cutoff,
        "diasUteisTotal": dias_uteis_total,
        "diasUteisDecorridos": dias_uteis_decorridos,
        "diasUteisRestantes": dias_uteis_total - dias_uteis_decorridos,
        "pctMtd": (dias_uteis_decorridos / dias_uteis_total) if dias_uteis_total else 0,
    }


def effective_status(call, hoje_iso):
    """Regra de auto-transição (seção 9 do CLAUDE.md): só quando a data da
    call é estritamente anterior a hoje — nunca no próprio dia da call."""
    if call["status"] == "a_realizar" and call.get("data") and call["data"] < hoje_iso:
        return "realizada"
    return call["status"]


def is_presales(call, presales_nome_lower):
    """Envolvimento de pré-vendas = agendado pelo Vinicius, qualquer origem
    (própria ou externa) — não exige canal próprio (seção 4 do CLAUDE.md,
    mesma definição usada no hero do painel)."""
    return presales_nome_lower in call["agendadoPor"].strip().lower()


def is_propria(call):
    return call.get("origemTipo") == "propria"


def status_of(ratio):
    """Mesmos thresholds do badge do painel: >90% verde, 70-90% âmbar,
    <70% vermelho (seção 5 do CLAUDE.md e seção 7 da spec de reports)."""
    if ratio > 0.9:
        return {"emoji": "🟢", "css": "green"}
    if ratio >= 0.7:
        return {"emoji": "🟡", "css": "amber"}
    return {"emoji": "🔴", "css": "red"}


def month_metrics(mes_key, state, taxonomia, feriados_set, hoje):
    """Agregados de um mês a partir da lista mestra crua (data/*.json), já
    com a transição a_realizar→realizada aplicada (ao vivo, com "hoje" do
    cron) — igual ao que o painel faz no navegador. Usado pelos dois reports.
    """
    hoje_iso = iso_of(hoje)
    presales_nome = taxonomia["presales_agendador"].strip().lower()
    meta = taxonomia["meta_mensal"]

    calls = [dict(c, status=effective_status(c, hoje_iso)) for c in state["calls"]]

    presales_calls = [c for c in calls if is_presales(c, presales_nome)]
    presales_realizadas = [c for c in presales_calls if c["status"] == "realizada"]
    presales_ns = [c for c in presales_realizadas if c["noShow"]]
    presales_real_total = len(presales_realizadas) - len(presales_ns)
    presales_ar = len([c for c in presales_calls if c["status"] == "a_realizar"])

    total_realizadas = [c for c in calls if c["status"] == "realizada"]
    total_ns = [c for c in total_realizadas if c["noShow"]]
    total_real = len(total_realizadas) - len(total_ns)
    total_ar = len([c for c in calls if c["status"] == "a_realizar"])

    def pct(n, total):
        return round((n / total) * 100) if total else 0

    return {
        "mesKey": mes_key,
        "meta": meta,
        "calls": calls,
        "presalesRealTotal": presales_real_total,
        "presalesAr": presales_ar,
        "presalesRealizadasCount": len(presales_realizadas),
        "presalesNsCount": len(presales_ns),
        "totalReal": total_real,
        "totalNs": len(total_ns),
        "totalAr": total_ar,
        "totalGeral": total_real + len(total_ns) + total_ar,
        "nsTotalPct": pct(len(total_ns), len(total_realizadas)),
        "nsPvPct": pct(len(presales_ns), len(presales_realizadas)),
    }
