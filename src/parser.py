"""Parser: converte texto colado (formato compacto ou mensagem do Slack, seção 2 e 8
do CLAUDE.md) no modelo interno de call. Aceita os dois formatos misturados ou não.
"""
import re
import uuid
import datetime

from . import taxonomy as tax

COMPACT_RE = re.compile(
    r'^(?P<empresa>.+?)\s*[—-]\s*(?P<data>\d{2}/\d{2})\s*[—-]\s*(?P<origem>.+?)\s*[—-]\s*'
    r'(?P<canal>.+?)\s*\(Agendada por @(?P<pessoa>[^)]+)\)\s*(?P<noshow>NO-SHOW)?\s*$'
)

SLACK_FIELD_RE = {
    "data": re.compile(r'Data da reuni[aã]o:\s*(\d{2}/\d{2})'),
    "contato": re.compile(r'Contato:\s*(.+)'),
    "cargo": re.compile(r'Cargo:\s*(.+)'),
    "empresa": re.compile(r'Empresa:\s*(.+)'),
    "origem": re.compile(r'Origem do lead:\s*(.+)'),
    "canal": re.compile(r'Canal de agendamento:\s*(.+)'),
    "vendedor": re.compile(r'Vendedor:\s*(.+)'),
    "pipedrive": re.compile(r'Link do Pipedrive:\s*(.+)'),
}


def _make_call(empresa, data_iso, origem_raw, canal_raw, agendado_por, no_show,
               pipedrive_id=None, contato=None, cargo=None, raw="", taxonomia=None):
    taxonomia = taxonomia or tax.load_taxonomia()
    origem, origem_ok = tax.normalize_origem(origem_raw, taxonomia)
    canal, canal_ok = tax.normalize_canal(canal_raw, taxonomia)
    return {
        "id": uuid.uuid4().hex[:8],
        "empresa": empresa.strip(),
        "data": data_iso,
        "origem": origem,
        "origemReconhecida": origem_ok,
        "origemTipo": tax.origem_tipo(origem, taxonomia),
        "canal": canal,
        "canalReconhecido": canal_ok,
        "agendadoPor": agendado_por.strip(),
        "status": "realizada" if no_show else "a_realizar",
        "noShow": bool(no_show),
        "pipedriveId": pipedrive_id,
        "contato": contato.strip() if contato else None,
        "cargo": cargo.strip() if cargo else None,
        "raw": raw.strip(),
        "criadoEm": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def _ddmm_to_iso(ddmm, ano):
    dia, mes = ddmm.split("/")
    return f"{ano:04d}-{int(mes):02d}-{int(dia):02d}"


def parse_compact_line(line, ano=None, taxonomia=None):
    ano = ano or datetime.date.today().year
    m = COMPACT_RE.match(line.strip())
    if not m:
        return None
    d = m.groupdict()
    data_iso = _ddmm_to_iso(d["data"], ano)
    return _make_call(
        empresa=d["empresa"],
        data_iso=data_iso,
        origem_raw=d["origem"],
        canal_raw=d["canal"],
        agendado_por=d["pessoa"],
        no_show=bool(d["noshow"]),
        raw=line,
        taxonomia=taxonomia,
    )


def parse_slack_block(block, ano=None, taxonomia=None):
    ano = ano or datetime.date.today().year
    fields = {}
    for key, rx in SLACK_FIELD_RE.items():
        m = rx.search(block)
        if m:
            fields[key] = m.group(1).strip()
    if "empresa" not in fields or "data" not in fields:
        return None

    canal_raw = fields.get("canal", "")
    canal_principal = re.split(r'\s*-\s*', canal_raw, maxsplit=1)[0].strip()
    if canal_principal.lower() in ("associada", "associado"):
        canal_principal = "Associados"

    vendedor_raw = fields.get("vendedor", "")
    nome_match = re.search(r'@([^\]\(]+)', vendedor_raw)
    agendado_por = nome_match.group(1).strip() if nome_match else vendedor_raw.strip()

    pipedrive_url = fields.get("pipedrive", "")
    pid_match = re.search(r'(\d+)\s*$', pipedrive_url)
    pipedrive_id = pid_match.group(1) if pid_match else None

    data_iso = _ddmm_to_iso(fields["data"], ano)

    return _make_call(
        empresa=fields["empresa"],
        data_iso=data_iso,
        origem_raw=fields.get("origem", ""),
        canal_raw=canal_principal,
        agendado_por=agendado_por,
        no_show=False,
        pipedrive_id=pipedrive_id,
        contato=fields.get("contato"),
        cargo=fields.get("cargo"),
        raw=block,
        taxonomia=taxonomia,
    )


def parse_bulk(text, ano=None, taxonomia=None):
    """Aceita um bloco de texto: várias linhas no formato compacto, OU uma/várias
    mensagens do Slack (delimitadas por 'NOVA CALL AGENDADA'). Não mistura os dois
    modos no mesmo texto — se houver marcador do Slack, tudo é tratado como Slack.
    """
    taxonomia = taxonomia or tax.load_taxonomia()
    ano = ano or datetime.date.today().year
    calls = []
    errors = []

    if "NOVA CALL AGENDADA" in text:
        chunks = text.split("NOVA CALL AGENDADA")[1:]
        for chunk in chunks:
            call = parse_slack_block(chunk, ano=ano, taxonomia=taxonomia)
            if call:
                calls.append(call)
            else:
                errors.append(("slack", chunk.strip()[:160]))
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            call = parse_compact_line(line, ano=ano, taxonomia=taxonomia)
            if call:
                calls.append(call)
            else:
                errors.append(("compacto", line[:160]))

    return calls, errors
