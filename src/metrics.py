"""Payload bruto por mês: uma lista de calls com os campos que a UI precisa
(empresa, data, origem, canal, origemTipo, agendadoPor já com apelido, se é
call de pré-vendas, status literal e no-show) mais label/meta do mês.

Tudo que depende de "hoje" — dias úteis/MTD, a transição a_realizar→realizada,
hero, badge, breakdowns e as tabelas — é calculado no navegador (dashboard.py,
bloco JS), ao vivo, com o relógio de quem está olhando a página. Nada disso
roda mais aqui nem é persistido (seções 4, 5 e 9 do CLAUDE.md).
"""
from . import taxonomy as tax

MESES_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _call_payload(c, presales_nome, taxonomia):
    return {
        "data": c["data"],
        "empresa": c["empresa"],
        "origem": c["origem"],
        "canal": c["canal"],
        "origemTipo": c.get("origemTipo"),
        "agendadoPor": tax.apelido_pessoa(c["agendadoPor"], taxonomia),
        "presales": presales_nome in c["agendadoPor"].strip().lower(),
        "status": c["status"],
        "noShow": bool(c["noShow"]),
    }


def compute_month_payload(mes_key, state, taxonomia):
    ano, mes_num = (int(x) for x in mes_key.split("-"))
    presales_nome = taxonomia["presales_agendador"].strip().lower()
    return {
        "label": f"{MESES_PT[mes_num]} {ano}",
        "meta": taxonomia["meta_mensal"],
        "calls": [_call_payload(c, presales_nome, taxonomia) for c in state["calls"]],
    }


def compute_all_months(months_data, taxonomia, feriados_todos, max_hist=12):
    """months_data: lista de (mes_key, state) em ordem cronológica ascendente."""
    months_payload = {
        mes_key: compute_month_payload(mes_key, state, taxonomia)
        for mes_key, state in months_data
    }
    ordered_keys = [k for k, _ in months_data]
    return {
        "months": months_payload,
        "histOrder": ordered_keys[-max_hist:],
        # None = sem override: o navegador escolhe o mês corrente ao vivo
        # (initApp/pickDefaultMes em dashboard.py), não "o último mês salvo"
        # — isso é o que evita abrir num mês futuro vazio só porque uma call
        # foi importada adiantada (seção 5 do CLAUDE.md). Só fica não-None
        # quando `gerar --mes` força explicitamente qual mês abre.
        "defaultMes": None,
        "allKeys": ordered_keys,
        "feriados": feriados_todos,
    }
