"""Cálculos de negócio: dias úteis/MTD, hero (canal próprio ∩ pré-vendas), no-show,
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
    dias_uteis_total = business_days(inicio, fim, feriados_set)
    dias_uteis_decorridos = business_days(inicio, cutoff_no_mes, feriados_set)
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
        return tax.origem_tipo(c["origem"], taxonomia) == "propria"

    def is_presales(c):
        return presales_nome in c["agendadoPor"].strip().lower()

    def apelido(c):
        return tax.apelido_pessoa(c["agendadoPor"], taxonomia)

    total_a_realizar = [c for c in calls if c["status"] == "a_realizar"]
    closed = len(total_a_realizar) == 0

    hero_calls = [c for c in calls if is_propria(c) and is_presales(c)]
    hero_real = sum(1 for c in hero_calls if c["status"] == "realizada" and not c["noShow"])
    hero_ns = sum(1 for c in hero_calls if c["status"] == "realizada" and c["noShow"])
    hero_ar = sum(1 for c in hero_calls if c["status"] == "a_realizar")

    propria_calls = [c for c in calls if is_propria(c)]
    externa_calls = [c for c in calls if not is_propria(c)]
    propria_real_total = sum(1 for c in propria_calls if c["status"] == "realizada" and not c["noShow"])
    outros_propria = propria_real_total - hero_real

    presales_calls = [c for c in calls if is_presales(c)]
    presales_realizadas = [c for c in presales_calls if c["status"] == "realizada"]
    presales_ns = [c for c in presales_realizadas if c["noShow"]]
    total_realizadas = [c for c in calls if c["status"] == "realizada"]
    total_ns = [c for c in total_realizadas if c["noShow"]]

    ns_total_pct = round((len(total_ns) / len(total_realizadas)) * 100) if total_realizadas else 0
    ns_pv_pct = round((len(presales_ns) / len(presales_realizadas)) * 100) if presales_realizadas else 0
    presales_real_total = len(presales_realizadas) - len(presales_ns)

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
        "prevendasReal": hero_real,
        "outrosPropria": outros_propria,
        "pvNoshow": hero_ns,
        "pvArealizar": hero_ar,
        "ns": {"total": ns_total_pct, "pv": ns_pv_pct},
        "presalesRealTotal": presales_real_total,
        "totalReal": len(total_realizadas) - len(total_ns),
        "totalNs": len(total_ns),
        "totalAr": len(total_a_realizar),
        "origem": {
            "CANAIS PRÓPRIOS": _tri_breakdown("origem", propria_calls),
            "CANAIS EXTERNOS": _tri_breakdown("origem", externa_calls),
        },
        "canal": _tri_breakdown("canal", calls),
        "pessoa": pessoa_rows,
    }

    if closed:
        view["mtdLine"] = "Mês encerrado"
        todas = sorted(calls, key=lambda c: c["data"])
        view["allCalls"] = [
            [_ddmm(c["data"]), c["empresa"], c["origem"], c["canal"], apelido(c), bool(c["noShow"])]
            for c in todas
        ]
    else:
        mtd = compute_mtd(mes_key, hoje, feriados_todos)
        linha = (
            f'MTD {_ddmm(mtd["cutoff"].isoformat())} · {mtd["dias_uteis_decorridos"]} de '
            f'{mtd["dias_uteis_total"]} dias úteis (até {_ddmm(mtd["cutoff"].isoformat())})'
        )
        if mtd["feriados_no_mes"]:
            linha += " · feriados: " + ", ".join(_ddmm(f) for f in mtd["feriados_no_mes"])
        view["mtdLine"] = linha
        view["expected"] = mtd["pct_mtd"] * meta

        inicio_semana = hoje - datetime.timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + datetime.timedelta(days=6)
        semana_calls = sorted(
            (c for c in total_a_realizar if inicio_semana <= _to_date(c["data"]) <= fim_semana),
            key=lambda c: c["data"],
        )
        view["week"] = {
            "title": (
                f'Pipeline desta semana ({_ddmm(inicio_semana.isoformat())}–'
                f'{_ddmm(fim_semana.isoformat())}) · {len(semana_calls)} calls'
            ),
            "calls": [
                [_ddmm(c["data"]), c["empresa"], c["origem"], c["canal"], apelido(c)]
                for c in semana_calls
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
