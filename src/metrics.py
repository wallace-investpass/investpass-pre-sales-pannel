"""Cálculos de negócio: dias úteis/MTD, hero (agendado pela pré-vendas, qualquer origem), no-show,
breakdowns por canal (3 categorias mutuamente exclusivas: real/a-realizar/no-show),
tabela de calls e payload combinado de todos os meses (seções 4, 5, 9, 10 do CLAUDE.md).
"""
import datetime
from collections import defaultdict

from . import taxonomy as tax

MESES_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _to_date(iso):
    return datetime.date.fromisoformat(iso)


def _ddmm(iso):
    d = _to_date(iso)
    return f"{d.day:02d}/{d.month:02d}"


def _ddmm_or_dash(iso):
    return _ddmm(iso) if iso else "—"


def business_days(d1, d2, feriados_set):
    if d1 > d2:
        return 0
    n = 0
    d = d1
    while d <= d2:
        if d.weekday() < 5 and d.isoformat() not in feriados_set:
            n += 1
        d += datetime.timedelta(days=1)
    return n


def mtd_cutoff(hoje):
    """Última sexta-feira até hoje, ou o próprio dia se hoje for sexta (seção 4)."""
    dias_desde_sexta = (hoje.weekday() - 4) % 7
    return hoje - datetime.timedelta(days=dias_desde_sexta)


def month_bounds(mes):
    ano, m = (int(x) for x in mes.split("-"))
    inicio = datetime.date(ano, m, 1)
    if m == 12:
        fim = datetime.date(ano, 12, 31)
    else:
        fim = datetime.date(ano, m + 1, 1) - datetime.timedelta(days=1)
    return inicio, fim


def compute_mtd(mes, hoje, feriados_todos):
    inicio, fim = month_bounds(mes)
    feriados_set = set(feriados_todos)
    cutoff = mtd_cutoff(hoje)
    cutoff_no_mes = min(max(cutoff, inicio), fim)
    ontem = hoje - datetime.timedelta(days=1)
    dias_uteis_total = business_days(inicio, fim, feriados_set)
    # dias úteis decorridos nunca inclui hoje — só dias 100% completos, mesmo
    # quando o cutoff (última sexta, ou hoje se hoje for sexta) cai em cima de hoje.
    dias_uteis_decorridos = business_days(inicio, min(cutoff_no_mes, ontem), feriados_set)
    feriados_no_mes = [f for f in feriados_todos if inicio.isoformat() <= f <= fim.isoformat()]
    return {
        "cutoff": cutoff_no_mes,
        "dias_uteis_total": dias_uteis_total,
        "dias_uteis_decorridos": dias_uteis_decorridos,
        "feriados_no_mes": feriados_no_mes,
        "pct_mtd": (dias_uteis_decorridos / dias_uteis_total) if dias_uteis_total else 0,
    }


def _tri_breakdown(chave, universo):
    """Cada linha vira [nome, realizada(sem no-show), a_realizar, no_show] — três
    categorias mutuamente exclusivas, soma = total (usadas nas barras de 3 tons)."""
    agrupado = defaultdict(lambda: {"real": 0, "ar": 0, "ns": 0})
    for c in universo:
        g = agrupado[c[chave]]
        if c["status"] == "realizada":
            if c["noShow"]:
                g["ns"] += 1
            else:
                g["real"] += 1
        else:
            g["ar"] += 1
    linhas = [[nome, g["real"], g["ar"], g["ns"]] for nome, g in agrupado.items()]
    linhas.sort(key=lambda x: -(x[1] + x[2] + x[3]))
    return linhas


def compute_month_view(mes_key, state, taxonomia, feriados_todos, hoje):
    calls = state["calls"]
    meta = taxonomia["meta_mensal"]
    presales_nome = taxonomia["presales_agendador"].strip().lower()

    def is_propria(c):
        return c.get("origemTipo") == "propria"

    def is_presales(c):
        return presales_nome in c["agendadoPor"].strip().lower()

    def apelido(c):
        return tax.apelido_pessoa(c["agendadoPor"], taxonomia)

    total_a_realizar = [c for c in calls if c["status"] == "a_realizar"]
    closed = len(total_a_realizar) == 0

    # "Envolvimento de pré-vendas" (hero) = agendado por Vinicius, qualquer origem
    # (própria ou externa) — seção 4 revisada. O card "canais próprios" abaixo é uma
    # métrica separada e não depende dessa definição.
    presales_calls = [c for c in calls if is_presales(c)]
    presales_realizadas = [c for c in presales_calls if c["status"] == "realizada"]
    presales_ns = [c for c in presales_realizadas if c["noShow"]]
    presales_ar = sum(1 for c in presales_calls if c["status"] == "a_realizar")
    presales_real_total = len(presales_realizadas) - len(presales_ns)

    propria_calls = [c for c in calls if is_propria(c)]
    externa_calls = [c for c in calls if not is_propria(c)]
    propria_real_total = sum(1 for c in propria_calls if c["status"] == "realizada" and not c["noShow"])
    propria_ns = sum(1 for c in propria_calls if c["status"] == "realizada" and c["noShow"])
    propria_ar = sum(1 for c in propria_calls if c["status"] == "a_realizar")
    externa_ar = sum(1 for c in externa_calls if c["status"] == "a_realizar")

    origem_disponivel = any(c["origem"] for c in calls)
    canal_disponivel = any(c["canal"] for c in calls)

    total_realizadas = [c for c in calls if c["status"] == "realizada"]
    total_ns = [c for c in total_realizadas if c["noShow"]]

    ns_total_pct = round((len(total_ns) / len(total_realizadas)) * 100) if total_realizadas else 0
    ns_pv_pct = round((len(presales_ns) / len(presales_realizadas)) * 100) if presales_realizadas else 0

    pessoas = defaultdict(lambda: {"real": 0, "ar": 0, "ns": 0})
    for c in calls:
        g = pessoas[apelido(c)]
        if c["status"] == "realizada":
            if c["noShow"]:
                g["ns"] += 1
            else:
                g["real"] += 1
        else:
            g["ar"] += 1
    pessoa_rows = [[nome, g["real"], g["ar"], g["ns"]] for nome, g in pessoas.items()]
    pessoa_rows.sort(key=lambda x: -(x[1] + x[2] + x[3]))

    ano, mes_num = (int(x) for x in mes_key.split("-"))
    label = f"{MESES_PT[mes_num]} {ano}"

    view = {
        "label": label,
        "closed": closed,
        "meta": meta,
        "prevendasReal": presales_real_total,
        "pvNoshow": len(presales_ns),
        "pvArealizar": presales_ar,
        "ns": {"total": ns_total_pct, "pv": ns_pv_pct},
        "presalesRealTotal": presales_real_total,
        "totalReal": len(total_realizadas) - len(total_ns),
        "totalNs": len(total_ns),
        "totalAr": len(total_a_realizar),
        "propriaRealTotal": propria_real_total,
        "propriaNs": propria_ns,
        "propriaAr": propria_ar,
        "externaAr": externa_ar,
        "origemDisponivel": origem_disponivel,
        "canalDisponivel": canal_disponivel,
        "origem": {
            "CANAIS PRÓPRIOS": _tri_breakdown("origem", propria_calls) if origem_disponivel else [],
            "CANAIS EXTERNOS": _tri_breakdown("origem", externa_calls) if origem_disponivel else [],
        },
        "canal": _tri_breakdown("canal", calls) if canal_disponivel else [],
        "pessoa": pessoa_rows,
    }

    if closed:
        view["mtdLine"] = "Mês encerrado"
        todas = sorted(calls, key=lambda c: c["data"] or "")
        view["allCalls"] = [
            [_ddmm_or_dash(c["data"]), c["empresa"], c["origem"] or "—", c["canal"] or "—", apelido(c), bool(c["noShow"])]
            for c in todas
        ]
    else:
        mtd = compute_mtd(mes_key, hoje, feriados_todos)
        view["mtdLine"] = (
            f'MTD {_ddmm(mtd["cutoff"].isoformat())} · {mtd["dias_uteis_decorridos"]} de '
            f'{mtd["dias_uteis_total"]} dias úteis (até {_ddmm(mtd["cutoff"].isoformat())})'
        )
        view["expected"] = mtd["pct_mtd"] * meta

        mes_a_realizar = sorted(total_a_realizar, key=lambda c: c["data"] or "")
        titulo_mes = label.replace(" ", "/")
        view["week"] = {
            "title": f"Pipeline do mês ({titulo_mes}) · {len(mes_a_realizar)} calls",
            "calls": [
                [_ddmm_or_dash(c["data"]), c["empresa"], c["origem"] or "—", c["canal"] or "—", apelido(c)]
                for c in mes_a_realizar
            ],
        }

    return view


def compute_all_months(months_data, taxonomia, feriados_todos, hoje=None, max_hist=12):
    """months_data: lista de (mes_key, state) em ordem cronológica ascendente."""
    hoje = hoje or datetime.date.today()
    months_payload = {
        mes_key: compute_month_view(mes_key, state, taxonomia, feriados_todos, hoje)
        for mes_key, state in months_data
    }
    ordered_keys = [k for k, _ in months_data]
    return {
        "months": months_payload,
        "histOrder": ordered_keys[-max_hist:],
        "defaultMes": ordered_keys[-1] if ordered_keys else None,
        "allKeys": ordered_keys,
    }
