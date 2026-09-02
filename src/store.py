"""Lista mestra persistida por mês (seção 9 do CLAUDE.md) — fonte de verdade única.
O dashboard é sempre gerado a partir daqui, nunca do texto colado diretamente.
"""
import json
import re
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_MES_RE = re.compile(r'^\d{4}-\d{2}$')


def month_file(mes):
    return DATA_DIR / f"{mes}.json"


def list_months():
    """Meses com arquivo salvo em data/, em ordem cronológica ascendente."""
    if not DATA_DIR.exists():
        return []
    chaves = [p.stem for p in DATA_DIR.glob("*.json") if _MES_RE.match(p.stem)]
    return sorted(chaves)


def load_month(mes):
    path = month_file(mes)
    if not path.exists():
        return {"mes": mes, "calls": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_month(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = month_file(state["mes"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _check_duplicates(existing_calls, new_call):
    warnings = []
    empresa_norm = new_call["empresa"].strip().lower()
    for c in existing_calls:
        if c["empresa"].strip().lower() != empresa_norm:
            continue
        if c["data"] == new_call["data"]:
            warnings.append(
                f"possível duplicata exata: '{new_call['empresa']}' já tem registro em {new_call['data']}"
            )
        else:
            warnings.append(
                f"'{new_call['empresa']}' já tem registro em outra data ({c['data']}) — reagendamento?"
            )
    return warnings


def add_call(mes, call):
    """Adiciona uma call à lista mestra do mês. Nunca bloqueia por causa das
    validações da seção 6 — só devolve avisos para quem chamou decidir o que fazer.
    """
    state = load_month(mes)
    warnings = _check_duplicates(state["calls"], call)
    if not call["origemReconhecida"]:
        warnings.append(f"origem desconhecida: '{call['origem']}' — adicionada mesmo assim, revisar taxonomia")
    if not call["canalReconhecido"]:
        warnings.append(f"canal desconhecido: '{call['canal']}' — adicionada mesmo assim, revisar taxonomia")
    state["calls"].append(call)
    save_month(state)
    return call, warnings


def add_calls_bulk(mes, calls):
    return [add_call(mes, call) for call in calls]


def find_calls(mes, empresa, data=None, pipedrive_id=None):
    state = load_month(mes)
    matches = []
    if pipedrive_id:
        matches = [c for c in state["calls"] if c.get("pipedriveId") == pipedrive_id]
        return state, matches
    empresa_norm = empresa.strip().lower()
    for c in state["calls"]:
        if empresa_norm in c["empresa"].strip().lower():
            if data is None or c["data"] == data:
                matches.append(c)
    return state, matches


def _ambiguous_msg(matches, campo_para_desambiguar):
    opcoes = "; ".join(f"{m['empresa']} em {m['data']} (id {m['id']})" for m in matches)
    return f"mais de uma call encontrada, especifique {campo_para_desambiguar} ou --pipedrive-id: {opcoes}"


def mark_no_show(mes, empresa, data=None, pipedrive_id=None):
    state, matches = find_calls(mes, empresa, data, pipedrive_id)
    if len(matches) == 0:
        return None, "nenhuma call encontrada"
    if len(matches) > 1:
        return None, _ambiguous_msg(matches, "--data")
    call = matches[0]
    call["status"] = "realizada"
    call["noShow"] = True
    save_month(state)
    return call, None


def _ddmm_to_iso(ddmm, ano):
    dia, mes = ddmm.split("/")
    return f"{ano:04d}-{int(mes):02d}-{int(dia):02d}"


def change_date(mes, empresa, nova_data_ddmm, ano=None, data_atual=None, pipedrive_id=None):
    """Muda a data de uma call. Se a nova data cair em outro mês, a call sai da
    lista mestra atual e vai para a do mês de destino (seção 4 — reagendamento
    entre meses)."""
    ano = ano or datetime.date.today().year
    state, matches = find_calls(mes, empresa, data_atual, pipedrive_id)
    if len(matches) == 0:
        return None, mes, "nenhuma call encontrada"
    if len(matches) > 1:
        return None, mes, _ambiguous_msg(matches, "--data-atual")

    call = matches[0]
    nova_data_iso = _ddmm_to_iso(nova_data_ddmm, ano)
    novo_mes_key = nova_data_iso[:7]
    call["data"] = nova_data_iso

    if novo_mes_key != mes:
        state["calls"] = [c for c in state["calls"] if c["id"] != call["id"]]
        save_month(state)
        destino = load_month(novo_mes_key)
        destino["calls"].append(call)
        save_month(destino)
        return call, novo_mes_key, None

    save_month(state)
    return call, mes, None


def auto_flip_status(mes, hoje=None):
    """Regra automática de virada de status (seção 9): toda call 'a_realizar' cuja
    data já passou e que não foi marcada como no-show vira 'realizada'."""
    hoje = hoje or datetime.date.today()
    state = load_month(mes)
    changed = 0
    for c in state["calls"]:
        if c["status"] == "a_realizar":
            call_date = datetime.date.fromisoformat(c["data"])
            if call_date < hoje:
                c["status"] = "realizada"
                changed += 1
    if changed:
        save_month(state)
    return state, changed
