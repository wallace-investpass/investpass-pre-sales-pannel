"""Cliente mínimo da Web API do Slack (chat.postMessage via Bot Token) para os
jobs de report (spec-prevendas-reports.md). Sem dependência externa — só stdlib.

Regras de falha (decididas em 2026-09-03, fora da spec original):
- Post no canal: até 3 tentativas com backoff exponencial antes de desistir.
- Se todas as tentativas falharem, manda DM pro dono (OWNER_USER_ID) avisando
  do erro, usando o mesmo bot token.
"""
import json
import time
import urllib.request
import urllib.error

BASE_URL = "https://slack.com/api/"


class SlackError(Exception):
    pass


def _call(token, method, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + method,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("ok"):
        raise SlackError(data.get("error", "erro desconhecido da API do Slack"))
    return data


def auth_test(token):
    """Chama auth.test — valida o token sem postar nada em lugar nenhum.
    Devolve {team, user, bot_id, ...} quando o token é válido."""
    return _call(token, "auth.test", {})


def post_message(token, channel, text, blocks=None, retries=3, backoff_base=2):
    """Posta uma mensagem, com retry exponencial (2s, 4s, 8s...). Lança
    SlackError se todas as tentativas falharem."""
    payload = {"channel": channel, "text": text}
    if blocks is not None:
        payload["blocks"] = blocks

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return _call(token, "chat.postMessage", payload)
        except (SlackError, urllib.error.URLError, TimeoutError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff_base ** attempt)
    raise SlackError(str(last_error))


def list_recent_messages(token, channel, limit=20):
    """conversations.history — usado só pra achar uma mensagem específica
    pra apagar (ex: post indo parar no canal errado). Não faz parte do
    fluxo normal dos reports."""
    data = _call(token, "conversations.history", {"channel": channel, "limit": limit})
    return data.get("messages", [])


def delete_message(token, channel, ts):
    return _call(token, "chat.delete", {"channel": channel, "ts": ts})


def notify_owner(token, owner_user_id, text):
    """DM de última instância pro dono do painel — usada quando o post no
    canal falhou de vez, ou quando o job não tem dado pra reportar. Melhor
    esforço: se essa DM também falhar, não faz sentido tentar de novo (o
    chamador já loga o erro original de qualquer forma)."""
    try:
        _call(token, "chat.postMessage", {"channel": owner_user_id, "text": text})
    except (SlackError, urllib.error.URLError, TimeoutError) as e:
        print(f"[slack] falha ao mandar DM de aviso pro dono também: {e}")
