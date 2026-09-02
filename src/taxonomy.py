"""Carrega e normaliza a taxonomia de origens/canais (seção 3 do CLAUDE.md)."""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_taxonomia():
    with open(CONFIG_DIR / "taxonomia.json", encoding="utf-8") as f:
        return json.load(f)


def load_feriados():
    with open(CONFIG_DIR / "feriados.json", encoding="utf-8") as f:
        data = json.load(f)
    todos = []
    for chave, lista in data.items():
        if chave.startswith("_"):
            continue
        todos.extend(lista)
    return sorted(todos)


def _match_canonical(value, canonical_list):
    if value is None:
        return "", False
    v = value.strip()
    if not v:
        return "", False
    for c in canonical_list:
        if c.lower() == v.lower():
            return c, True
    return v, False


def normalize_origem(value, taxonomia):
    todas = taxonomia["origem_propria"] + taxonomia["origem_externa"]
    return _match_canonical(value, todas)


def normalize_canal(value, taxonomia):
    return _match_canonical(value, taxonomia["canal_agendamento"])


def origem_tipo(origem_canonico, taxonomia):
    if origem_canonico in taxonomia["origem_propria"]:
        return "propria"
    if origem_canonico in taxonomia["origem_externa"]:
        return "externa"
    return "desconhecida"


def apelido_pessoa(nome, taxonomia):
    apelidos = taxonomia.get("apelidos_pessoas", {})
    if nome in apelidos:
        return apelidos[nome]
    partes = [p for p in nome.strip().split() if p]
    return partes[0] if partes else nome
