"""Gera o dashboard HTML (tema claro, abas Detalhe mensal / Histórico) a partir do
payload combinado de todos os meses salvos — seções 5, 10 e 11 do CLAUDE.md.
Layout portado de `mockup-v3-painel-prevendas.html` (fonte de verdade de layout);
os dados fictícios do mockup são substituídos pelo payload real calculado em
`metrics.compute_all_months`, e a única lógica de cálculo que o mockup fazia no
client-side (expected/MTD, projeção) passou a vir pronta do servidor.
"""
import json


def _embed_json(value):
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def render(payload, generated_at=""):
    months_json = _embed_json(payload["months"])
    hist_order_json = _embed_json(payload["histOrder"])
    feriados_json = _embed_json(payload["feriados"])
    default_mes = payload["defaultMes"]

    options_html = ""
    for key in payload["allKeys"]:
        label = payload["months"][key]["label"]
        active = " active" if key == default_mes else ""
        options_html += f'<div class="month-dropdown-item{active}" data-mes="{key}" onclick="selectMonth(\'{key}\')">{label}</div>'
    default_label = payload["months"][default_mes]["label"] if default_mes else ""

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Painel de Pré-vendas — investPass</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;900&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">

  <div class="app-header">
    <div style="display:flex; align-items:flex-end; gap:10px;">
      <span style="font-weight:900; font-size:22px; letter-spacing:-0.02em;">investPass</span>
      <span style="width:1.5px; height:22px; background:var(--text-muted);"></span>
      <h1 style="display:inline; font-size:22px; font-weight:500; margin:0; line-height:22px;">Painel de Pré-Vendas</h1>
    </div>
    <span class="updated">última atualização: {generated_at}</span>
  </div>

  <div class="top-bar">
    <div class="tabs">
      <button class="tab active" data-tab="mensal" onclick="switchTab('mensal')">Detalhe mensal</button>
      <button class="tab" data-tab="historico" onclick="switchTab('historico')">Histórico</button>
    </div>
    <div class="ctrls">
    <div class="scope-seg" id="scope">
      <button type="button" data-s="pv" onclick="setScope('pv')">Pré-vendas</button>
      <button type="button" data-s="time" onclick="setScope('time')">Time</button>
    </div>
    <div class="month-dropdown" id="month-dropdown">
      <button type="button" class="month-dropdown-btn" id="month-dropdown-btn" onclick="toggleMonthDropdown()">
        <span id="month-dropdown-label">{default_label}</span>
        <span class="month-dropdown-chevron">▾</span>
      </button>
      <div class="month-dropdown-list" id="month-dropdown-list" hidden>
        {options_html}
      </div>
    </div>
    </div>
  </div>

  <div id="view-mensal">
    <div class="header-row">
      <span class="mtd-line" id="m-mtdline"></span>
    </div>

    <div id="m-strip"></div>
    <div id="m-hero"></div>
    <div id="m-cards"></div>

    <div class="seg-grid">
      <div class="card seg-card">
        <p class="title">🌱 Origem do lead</p>
        <div id="m-origem"></div>
        <div class="p-legend" id="m-origem-legend">
          <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
          <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
          <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
        </div>
      </div>
      <div class="card seg-card">
        <p class="title">📲 Canal de agendamento</p>
        <div id="m-canal"></div>
        <div class="p-legend" id="m-canal-legend">
          <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
          <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
          <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
        </div>
      </div>
    </div>

    <div id="m-actions"></div>

    <div class="card people-card" id="m-people-card">
      <p class="title">👤 Agendamentos por pessoa</p>
      <div id="m-pessoa"></div>
      <div class="p-legend">
        <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
        <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
        <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
      </div>
    </div>

    <div class="card week-card"><p class="title" id="m-week-title"></p><div id="m-week-body"></div></div>
    <div class="card week-card" id="m-realized-card"><p class="title" id="m-realized-title"></p><div id="m-realized-body"></div></div>
  </div>

  <div id="view-historico">
    <div class="card hist-card">
      <p class="title">Taxa de no-show MoM</p>
      <div id="chart-noshow"></div>
      <div class="legend">
        <span id="leg-ns-total"><span class="line-swatch" style="background:var(--text-secondary);"></span>No-show total</span>
        <span><span class="line-swatch" style="background:var(--g-dark);"></span>No-show pré-vendas</span>
        <span><span class="line-swatch dashed" style="border-top-color:#c9a29c;"></span>meta de no-show: 10%</span>
      </div>
    </div>
    <div class="card hist-card">
      <p class="title">Performance de pré-vendas MoM</p>
      <div id="chart-meta"></div>
      <div class="legend">
        <span><span class="dot" style="background:var(--g-dark);"></span>Agendado pela pré-vendas</span>
        <span id="leg-sem-pv"><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>Sem envolvimento de pré-vendas</span>
        <span><span class="line-swatch dashed" style="border-top-color:#a9a89f;"></span><span id="chart-meta-goal-legend"></span></span>
      </div>
    </div>
    <div class="card hist-card">
      <p class="title">Performance por Origem MoM</p>
      <div id="chart-origem"></div>
      <div class="legend" id="chart-origem-legend"></div>
    </div>
    <div class="card hist-card">
      <p class="title">Performance por Canal MoM</p>
      <div id="chart-canal"></div>
      <div class="legend" id="chart-canal-legend"></div>
    </div>
    <div class="card hist-card" id="hist-pessoa-card">
      <p class="title">Performance por Pessoa MoM</p>
      <div id="chart-pessoa"></div>
      <div class="legend" id="chart-pessoa-legend"></div>
    </div>
  </div>

</div>
<div id="chart-tip" class="chart-tip" hidden></div>
<script>
const MONTHS = {months_json};
const HIST_ORDER = {hist_order_json};
const FERIADOS = {feriados_json};
const DEFAULT_MES = {json.dumps(default_mes)};

{JS}

initApp();
</script>
</body>
</html>'''


CSS = '''
  :root {
    --surface-0:#F1F5F8; --surface-1:#ffffff; --text-primary:#1a1a18;
    --text-secondary:#6b6a63; --text-muted:#9a9990; --border:#e3e2db;
    --brand-green:#0ED555;
    --g-dark:#3f7a5c;   /* realizadas - sóbrio */
    --g-mid:#8fbf9e;    /* a realizar - sóbrio */
    --g-pale:#d9ebe0;   /* no-show - sóbrio */
    --green-bg:#e6f9ec; --green-text:#0a6b2b;
    --amber:#b5790e; --amber-bg:#faeeda;
    --red:#c0392b; --red-bg:#fcebeb;
    --blue:#1a5fb4; --blue-bg:#e8f0fc;
  }
  * { box-sizing:border-box; }
  body { margin:0; padding:32px; background:var(--surface-0); font-family:'Montserrat',sans-serif; color:var(--text-primary); }
  .wrap { max-width:1080px; margin:0 auto; }

  .app-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; flex-wrap:wrap; gap:8px; }
  .app-header .updated { font-size:12px; color:var(--text-muted); }

  .top-bar { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; flex-wrap:wrap; gap:10px; }
  .tabs { display:flex; gap:4px; border-bottom:0.5px solid var(--border); }
  .tab { padding:8px 4px; margin-right:20px; font-size:13.5px; font-weight:500; color:var(--text-muted); border-bottom:2px solid transparent; cursor:pointer; background:none; border-top:none; border-left:none; border-right:none; font-family:'Montserrat',sans-serif; }
  .tab.active { color:var(--text-primary); border-bottom:2px solid var(--text-primary); }
  .month-dropdown { position:relative; }
  .month-dropdown-btn { height:32px; border-radius:8px; border:0.5px solid var(--border); background:var(--surface-1); padding:0 10px; font-size:13px; font-family:'Montserrat',sans-serif; color:var(--text-primary); display:flex; align-items:center; gap:8px; cursor:pointer; }
  .month-dropdown-chevron { font-size:10px; color:var(--text-muted); }
  .month-dropdown-list {
    position:absolute; top:calc(100% + 4px); bottom:auto; left:0; right:0; min-width:180px;
    background:var(--surface-1); border:0.5px solid var(--border); border-radius:8px;
    box-shadow:0 8px 24px rgba(26,26,24,.14); max-height:280px; overflow-y:auto; z-index:20;
  }
  .month-dropdown-item { padding:8px 12px; font-size:13px; cursor:pointer; }
  .month-dropdown-item:hover { background:var(--surface-0); }
  .month-dropdown-item.active { font-weight:600; background:var(--surface-0); }

  .header-row { display:flex; align-items:baseline; justify-content:flex-end; margin-bottom:16px; flex-wrap:wrap; gap:6px; }
  .header-row .mtd-line { font-size:12px; color:var(--text-muted); }

  .card { background:var(--surface-1); border:0.5px solid var(--border); border-radius:12px; padding:18px 20px; margin-bottom:14px; }
  .hero { display:grid; grid-template-columns:minmax(260px,1fr) 1.6fr; gap:26px; align-items:start; }
  .hero-left { display:flex; flex-direction:column; align-items:flex-start; }
  .hero-label { font-size:11.5px; font-weight:600; color:var(--text-secondary); letter-spacing:0.02em; text-transform:uppercase; margin:0 0 14px; line-height:1.4; }
  .hero-num { font-size:72px; font-weight:600; line-height:1; margin:0 0 12px; }
  .badge { padding:5px 12px; border-radius:8px; font-size:12.5px; font-weight:600; white-space:nowrap; }
  .badge-green { background:var(--green-bg); color:var(--green-text); }
  .badge-amber { background:var(--amber-bg); color:var(--amber); }
  .badge-red { background:var(--red-bg); color:var(--red); }
  .meta-line { font-size:12px; color:var(--text-secondary); margin:12px 0 0; }
  .chart-wrap svg { display:block; }
  .strip { display:flex; align-items:center; justify-content:space-between; gap:20px; transition:box-shadow 150ms ease; }
  .strip:hover { box-shadow:0 0 0 1px #d8d6cb, 0 4px 14px rgba(26,26,24,.08); }
  .strip .s-label { font-size:11px; color:var(--text-muted); margin:0 0 2px; }
  .strip .s-val { font-size:28px; font-weight:600; margin:0; line-height:1.1; }
  .strip .s-sub { font-size:12px; color:var(--text-secondary); margin:2px 0 0; }
  .strip .s-items { display:flex; flex-direction:column; gap:6px; font-size:13px; }
  .strip .s-items b { font-weight:700; }
  .strip .s-covered { font-size:13px; }

  .ctrls { display:flex; align-items:center; gap:10px; }
  .scope-seg { display:inline-flex; background:var(--surface-1); border:0.5px solid var(--border); border-radius:9px; padding:3px; }
  .scope-seg button { border:none; background:none; padding:6px 14px; border-radius:7px; font:600 12.5px 'Montserrat',sans-serif; color:var(--text-muted); cursor:pointer; }
  .scope-seg button.on { background:var(--text-primary); color:#fff; }
  .summary-grid { display:grid; gap:12px; margin-bottom:14px; grid-template-columns:repeat(var(--cols,4),1fr); }
  .card.metric-card { transition:box-shadow 150ms ease; display:flex; flex-direction:column; }
  .card.metric-card:hover { box-shadow:0 0 0 1px #d8d6cb, 0 4px 14px rgba(26,26,24,.08); }
  .metric-card .label { font-size:12px; color:var(--text-secondary); margin:0 0 6px; font-weight:600; min-height:48px; }
  .metric-card .value-row { flex:1; display:flex; align-items:center; }
  .metric-card .value { font-size:30px; font-weight:500; margin:0; }
  .metric-card .value.red { color:var(--red); }
  .metric-card .sub { font-size:11px; color:var(--text-muted); margin:6px 0 0; }
  .vline { display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }
  .vline .vs { font-size:11.5px; color:var(--text-muted); }
  .twin { flex:1; display:flex; justify-content:space-between; align-items:center; gap:18px; }

  .seg-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
  .seg-card { display:flex; flex-direction:column; }
  .seg-card .title { font-size:13px; color:var(--text-secondary); margin:0 0 10px; font-weight:600; }
  .seg-card .p-legend { margin-top:auto; padding-top:12px; }
  .seg-section-label { font-size:10.5px; font-weight:700; color:var(--text-muted); letter-spacing:0.03em; margin:12px 0 6px; text-transform:uppercase; }
  .seg-section-label:first-of-type { margin-top:0; }
  .ch-row { display:flex; align-items:center; gap:8px; margin-bottom:4px; min-height:32px; border-radius:8px; padding:2px 6px; margin-left:-6px; margin-right:-6px; transition:background 150ms ease; }
  .ch-row:hover { background:var(--surface-0); }
  .ch-row .name { font-size:12px; width:120px; flex-shrink:0; }
  .ch-track { flex:1; background:var(--surface-0); border-radius:4px; height:8px; overflow:hidden; display:flex; }
  .ch-count { font-size:11px; width:150px; text-align:right; color:var(--text-muted); flex-shrink:0; line-height:1.45; }
  .ch-count .seg { white-space:nowrap; }

  .week-card .title { font-size:13px; font-weight:600; margin:0 0 10px; }
  .week-empty { color:var(--text-muted); font-size:12.5px; font-style:italic; }

  table.calls-table { width:100%; border-collapse:collapse; font-size:12px; }
  .calls-table-scroll { max-height:280px; overflow-y:auto; border:0.5px solid var(--border); border-radius:8px; }
  table.calls-table thead th { position:sticky; top:0; background:var(--surface-1); z-index:1; }
  table.calls-table th { text-align:left; padding:8px 10px; font-size:10.5px; text-transform:uppercase; color:var(--text-muted); border-bottom:0.5px solid var(--border); }
  table.calls-table td { padding:7px 10px; border-bottom:0.5px solid var(--border); }
  table.calls-table tbody tr:last-child td { border-bottom:none; }
  .ns-tag { background:var(--red-bg); color:var(--red); font-size:10px; padding:1px 6px; border-radius:5px; margin-left:6px; }
  .today-tag { background:#fdead9; color:#c1620a; font-size:9.5px; font-weight:600; text-transform:uppercase; letter-spacing:0.02em; padding:1px 6px; border-radius:5px; margin-left:6px; }
  .nsre-tag { background:#e3eefb; color:#185fa5; font-size:10px; padding:1px 6px; border-radius:5px; margin-left:6px; white-space:nowrap; }
  .plink { color:#185fa5; text-decoration:none; font-weight:500; }
  .plink.off { color:#b9b8ae; cursor:default; }
  .two-col { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
  .two-col .card { margin-bottom:0; }
  .badge-presales { background:var(--blue-bg); color:var(--blue); font-size:9.5px; font-weight:600; text-transform:uppercase; letter-spacing:0.02em; padding:1px 6px; border-radius:5px; margin-left:6px; white-space:nowrap; }

  .people-card .title { font-size:13px; font-weight:600; margin:0 0 10px; }
  .p-row { display:flex; align-items:center; gap:10px; margin-bottom:4px; min-height:32px; border-radius:8px; padding:2px 6px; margin-left:-6px; margin-right:-6px; transition:background 150ms ease; }
  .p-row:hover { background:var(--surface-0); }
  .p-row .name { font-size:12.5px; width:70px; flex-shrink:0; font-weight:500; }
  .p-track { flex:1; background:var(--surface-0); border-radius:4px; height:9px; overflow:hidden; display:flex; }
  .p-count { font-size:11.5px; width:210px; text-align:right; color:var(--text-muted); flex-shrink:0; line-height:1.45; }
  .p-count .seg { white-space:nowrap; }
  .p-legend { display:flex; gap:16px; margin-top:8px; font-size:11px; color:var(--text-secondary); }
  .p-legend span { display:flex; align-items:center; gap:5px; }
  .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

  .hist-card .title { font-size:13.5px; font-weight:600; margin:0 0 14px; }
  .legend { display:flex; gap:16px; margin-top:8px; font-size:11px; color:var(--text-secondary); flex-wrap:wrap; }
  .legend span { display:flex; align-items:center; gap:5px; }
  .line-swatch { width:14px; height:2px; display:inline-block; }
  .line-swatch.dashed { width:14px; height:0; background:none; border-top:2px dashed; }
  svg text { font-family:'Montserrat',sans-serif; }
  svg circle[data-tip] { transition:r 120ms ease; cursor:default; }
  svg circle[data-tip]:hover { r:4.5; }
  svg rect[data-tip] { transition:opacity 120ms ease; cursor:default; }
  svg rect[data-tip]:hover { opacity:0.78; }

  .chart-tip {
    position:fixed; pointer-events:none; z-index:1000;
    background:var(--text-primary); color:#fff; font-size:11px; font-weight:500;
    padding:5px 9px; border-radius:6px; white-space:nowrap;
    transform:translate(-50%, -100%); margin-top:-8px;
  }

  #view-historico { display:none; }

  @media (max-width:860px) {
    .summary-grid { grid-template-columns:1fr 1fr; }
    .seg-grid, .hero, .two-col { grid-template-columns:1fr; }
  }
'''

JS = r'''
// ---- Data/hora ao vivo (relógio de quem está olhando a página) ----------
// Tudo que depende de "hoje" — dias úteis/MTD, a transição a_realizar→
// realizada, hero, badge, breakdowns e tabelas — é calculado aqui, no
// carregamento da página e de novo se a aba ficar aberta atravessando a
// virada do dia (seção 9 do CLAUDE.md). Nunca é persistido: MONTHS guarda
// só o status literal salvo em data/*.json.

function parseIso(iso){
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

function isoOf(date){
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function todayIso(){
  return isoOf(new Date());
}

function ddmm(iso){
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

function ddmmOrDash(iso){
  return iso ? ddmm(iso) : '—';
}

function businessDays(d1, d2, feriadosSet){
  if (d1 > d2) return 0;
  let n = 0;
  const d = new Date(d1);
  while (d <= d2) {
    if (d.getDay() !== 0 && d.getDay() !== 6 && !feriadosSet.has(isoOf(d))) n++;
    d.setDate(d.getDate() + 1);
  }
  return n;
}

function mtdCutoffDate(hoje, feriadosSet){
  // Último dia útil completo anterior a hoje — pula fins de semana e
  // feriados, retrocedendo até achar um dia útil real. Nunca é o próprio
  // hoje, mesmo que hoje seja dia útil (seção 4).
  const d = new Date(hoje);
  d.setDate(d.getDate() - 1);
  while (d.getDay() === 0 || d.getDay() === 6 || feriadosSet.has(isoOf(d))) {
    d.setDate(d.getDate() - 1);
  }
  return d;
}

function monthBounds(mesKey){
  const [ano, m] = mesKey.split('-').map(Number);
  const inicio = new Date(ano, m - 1, 1);
  const fim = new Date(ano, m, 0);
  return [inicio, fim];
}

function computeMtd(mesKey, hoje, feriadosSet){
  const [inicio, fim] = monthBounds(mesKey);
  const cutoff = mtdCutoffDate(hoje, feriadosSet);
  const diasUteisTotal = businessDays(inicio, fim, feriadosSet);
  // Se o cutoff cair no mês anterior (início do mês, nenhum dia útil
  // completo decorrido ainda), decorridos é 0 — não força a data do
  // cutoff pro início do mês (isso contaria um dia fantasma).
  const diasUteisDecorridos = cutoff < inicio ? 0 : businessDays(inicio, cutoff < fim ? cutoff : fim, feriadosSet);
  return {
    cutoff,
    diasUteisTotal,
    diasUteisDecorridos,
    pctMtd: diasUteisTotal ? diasUteisDecorridos / diasUteisTotal : 0,
  };
}

// Regra de auto-transição (seção 9): só quando a data da call é estritamente
// anterior a hoje — nunca no próprio dia da call. Nunca muta o objeto original.
function effectiveCall(c, hojeIso){
  if (c.status === 'a_realizar' && c.data && c.data < hojeIso) {
    return Object.assign({}, c, { status: 'realizada' });
  }
  return c;
}

function triBreakdown(chave, universo){
  const agrupado = new Map();
  universo.forEach(c => {
    const nome = c[chave];
    if (!agrupado.has(nome)) agrupado.set(nome, { real: 0, ar: 0, ns: 0 });
    const g = agrupado.get(nome);
    if (c.status === 'realizada') {
      if (c.noShow) g.ns++; else g.real++;
    } else {
      g.ar++;
    }
  });
  const linhas = [...agrupado.entries()].map(([nome, g]) => [nome, g.real, g.ar, g.ns]);
  linhas.sort((a, b) => (b[1] + b[2] + b[3]) - (a[1] + a[2] + a[3]));
  return linhas;
}

function normName(s){
  return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

// Todas as calls de todos os meses carregados, de qualquer agendador — a busca
// de reagendamento (seção 5) nunca usa o filtro de escopo.
let ALL_CALLS = [];
function buildAllCalls(){
  ALL_CALLS = [];
  Object.keys(MONTHS).forEach(k => MONTHS[k].calls.forEach(c => {
    if (c.data) ALL_CALLS.push({ nome: normName(c.empresa), data: c.data, pid: c.pipedriveId || null });
  }));
}

// Data (ISO) da primeira call posterior da mesma empresa, ou null. Dois deals
// com pipedriveId diferentes são oportunidades distintas — não conta.
function reagendamentoDe(c){
  if (!c.data) return null;
  const nome = normName(c.empresa);
  let melhor = null;
  ALL_CALLS.forEach(o => {
    if (o.nome !== nome || o.data <= c.data) return;
    if (c.pipedriveId && o.pid && c.pipedriveId !== o.pid) return;
    if (melhor === null || o.data < melhor) melhor = o.data;
  });
  return melhor;
}

function bizDayList(inicio, fim, feriadosSet){
  const out = [];
  const d = new Date(inicio);
  while (d <= fim) {
    if (d.getDay() !== 0 && d.getDay() !== 6 && !feriadosSet.has(isoOf(d))) out.push(isoOf(d));
    d.setDate(d.getDate() + 1);
  }
  return out;
}

function statusOf(ratio){
  if (ratio > 0.9) return { css: 'green', label: '🟢' };
  if (ratio >= 0.7) return { css: 'amber', label: '🟡' };
  return { css: 'red', label: '🔴' };
}

const pct = (n, d) => d ? Math.round((n / d) * 100) : 0;

function callRow(c, hojeIso){
  return {
    data: ddmmOrDash(c.data), iso: c.data, empresa: c.empresa,
    origem: c.origem || '—', canal: c.canal || '—',
    pessoa: c.agendadoPor, presales: !!c.presales,
    noShow: !!c.noShow, hoje: c.data === hojeIso,
    pid: c.pipedriveId || null,
    resched: c.noShow ? reagendamentoDe(c) : null,
  };
}

function computeMonthView(mesKey, raw, hojeIso, feriadosSet, scope){
  const calls = raw.calls.map(c => effectiveCall(c, hojeIso));
  const meta = raw.meta;

  const totalARealizar = calls.filter(c => c.status === 'a_realizar');
  const closed = totalARealizar.length === 0;

  // Hero e faixa de projeção: sempre o número do pré-vendas (agendado pelo
  // Vinicius, qualquer origem), nos dois escopos.
  const pvc = calls.filter(c => c.presales);
  const pvRealizadas = pvc.filter(c => c.status === 'realizada');
  const pvNs = pvRealizadas.filter(c => c.noShow);
  const pvAr = pvc.filter(c => c.status === 'a_realizar');
  const prevendasReal = pvRealizadas.length - pvNs.length;

  const isPropria = c => c.origemTipo === 'propria';
  const totalRealizadas = calls.filter(c => c.status === 'realizada');
  const totalNs = totalRealizadas.filter(c => c.noShow);

  // Disponibilidade de dado é sempre do mês inteiro, nunca do recorte de escopo.
  const origemDisponivel = calls.some(c => c.origem);
  const canalDisponivel = calls.some(c => c.canal);
  const dataDisponivel = calls.every(c => c.data);

  // Universo do escopo: Pré-vendas filtra ANTES de calcular breakdowns/tabelas.
  const U = scope === 'pv' ? pvc : calls;
  const propriaU = U.filter(isPropria);
  const externaU = U.filter(c => !isPropria(c));

  const [inicio, fim] = monthBounds(mesKey);
  const bdays = bizDayList(inicio, fim, feriadosSet);
  const hojeDate = parseIso(hojeIso);
  const mtd = computeMtd(mesKey, hojeDate, feriadosSet);
  const dec = closed ? bdays.length : Math.min(mtd.diasUteisDecorridos, bdays.length);

  const view = {
    label: raw.label, closed, meta, scope,
    prevendasReal, pvArealizar: pvAr.length,
    presalesRealTotal: prevendasReal,
    ns: { total: pct(totalNs.length, totalRealizadas.length), pv: pct(pvNs.length, pvRealizadas.length) },
    pvNsCount: pvNs.length, pvRealizadasCount: pvRealizadas.length,
    totalReal: totalRealizadas.length - totalNs.length,
    totalNs: totalNs.length,
    totalAr: totalARealizar.length,
    propriaRealTotal: calls.filter(c => isPropria(c) && c.status === 'realizada' && !c.noShow).length,
    propriaNs: calls.filter(c => isPropria(c) && c.status === 'realizada' && c.noShow).length,
    propriaAr: calls.filter(c => isPropria(c) && c.status === 'a_realizar').length,
    externaAr: calls.filter(c => !isPropria(c) && c.status === 'a_realizar').length,
    pvHoje: pvc.filter(c => c.data === hojeIso && !c.noShow).length,
    origemDisponivel, canalDisponivel, dataDisponivel,
    origem: {
      'CANAIS PRÓPRIOS': origemDisponivel ? triBreakdown('origem', propriaU) : [],
      'CANAIS EXTERNOS': origemDisponivel ? triBreakdown('origem', externaU) : [],
    },
    canal: canalDisponivel ? triBreakdown('canal', U) : [],
    pessoa: triBreakdown('agendadoPor', calls),
    hojeIso,
    mtdLine: closed ? 'Mês encerrado' : '',
    diasUteisTotal: bdays.length,
    diasUteisRestantes: bdays.length - dec,
  };

  if (!closed) {
    const cutoffLabel = ddmm(isoOf(mtd.cutoff));
    view.mtdLine = `MTD ${cutoffLabel} · ${mtd.diasUteisDecorridos} de ${mtd.diasUteisTotal} dias úteis (até ${cutoffLabel})`;
    view.expected = mtd.pctMtd * meta;
  }

  // Curva do hero: eixo X = dias úteis do mês (mesma contagem do MTD).
  const cleanReal = pvRealizadas.filter(c => !c.noShow && c.data);
  const arDatadas = pvAr.filter(c => c.data);
  const n = bdays.length;
  const cumReal = bdays.map((d, i) => {
    if (i >= dec) return null;
    return (dec === n && i === n - 1) ? cleanReal.length : cleanReal.filter(c => c.data <= d).length;
  });
  const cumProj = bdays.map((d, i) => {
    if (i < dec) return cumReal[i];
    return i === n - 1 ? prevendasReal + pvAr.length : prevendasReal + arDatadas.filter(c => c.data <= d).length;
  });
  view.chart = { bdays, dec, cumReal, cumProj };

  const byDate = (a, b) => (a.data || '').localeCompare(b.data || '') || a.empresa.localeCompare(b.empresa);
  const tituloMes = raw.label.replace(' ', '/');
  if (closed) {
    const todas = [...U].sort(byDate);
    view.allCalls = todas.map(c => callRow(c, hojeIso));
    view.allTitle = `Todas as calls de ${raw.label}`;
  } else {
    const ar = U.filter(c => c.status === 'a_realizar').sort(byDate);
    view.week = {
      title: `Pipeline restante do mês (${tituloMes}) · ${ar.length} calls a realizar`,
      calls: ar.map(c => callRow(c, hojeIso)),
    };
    const re = U.filter(c => c.status === 'realizada').sort(byDate);
    view.realized = {
      title: `Calls já realizadas no mês (${tituloMes}) · ${re.length} calls realizadas (ou que deveriam ter sido)`,
      calls: re.map(c => callRow(c, hojeIso)),
    };
    // Tabelas de ação (só escopo Pré-vendas, mês aberto).
    view.pendentes = pvRealizadas.filter(c => c.noShow && !reagendamentoDe(c)).sort(byDate).map(c => callRow(c, hojeIso));
    view.hoje = pvc.filter(c => c.data === hojeIso && !c.noShow).sort(byDate).map(c => callRow(c, hojeIso));
  }
  return view;
}

let FERIADOS_SET;
let VIEWS = {};
let CURRENT_TODAY = null;
let ACTIVE_MES = null;
let ACTIVE_TAB = 'mensal';
// Escopo (seção 5): Pré-vendas por padrão; ?visao=time abre direto em Time.
// Não persiste a última escolha. É foco de leitura, não controle de acesso.
let SCOPE = new URLSearchParams(location.search).get('visao') === 'time' ? 'time' : 'pv';

function recomputeViews(){
  CURRENT_TODAY = todayIso();
  VIEWS = {};
  Object.keys(MONTHS).forEach(key => {
    VIEWS[key] = computeMonthView(key, MONTHS[key], CURRENT_TODAY, FERIADOS_SET, SCOPE);
  });
}

function checkDayRollover(){
  if (todayIso() === CURRENT_TODAY) return;
  recomputeViews();
  if (ACTIVE_MES) renderMonth(ACTIVE_MES);
  if (ACTIVE_TAB === 'historico') renderHistorico();
}

// Mês que o dropdown abre por padrão (seção 5 do CLAUDE.md): o mês corrente
// pelo relógio de quem está olhando a página — nunca "o último mês salvo"
// (um mês futuro com uma call adiantada não pode roubar o default do mês
// corrente). Se não houver arquivo salvo pro mês corrente, cai pro mês
// salvo mais recente ANTERIOR a ele; se nem isso existir (só há meses
// futuros salvos), cai pro mês salvo mais antigo disponível.
function pickDefaultMes(){
  const keys = Object.keys(MONTHS).sort();
  if (!keys.length) return null;
  const atual = CURRENT_TODAY.slice(0, 7);
  if (keys.includes(atual)) return atual;
  const anteriores = keys.filter(k => k < atual);
  if (anteriores.length) return anteriores[anteriores.length - 1];
  return keys[0];
}

function initApp(){
  FERIADOS_SET = new Set(FERIADOS);
  buildAllCalls();
  document.querySelectorAll('#scope button').forEach(b => b.classList.toggle('on', b.dataset.s === SCOPE));
  recomputeViews();
  const defaultKey = DEFAULT_MES || pickDefaultMes();
  if (defaultKey) renderMonth(defaultKey);
  initTooltips();
  setInterval(checkDayRollover, 60000);
}

function segBar(real, ar, ns){
  const total = real + ar + ns || 1;
  return `<div class="ch-track">
    <div style="width:${real/total*100}%; background:var(--g-dark);"></div>
    <div style="width:${ar/total*100}%; background:var(--g-mid);"></div>
    <div style="width:${ns/total*100}%; background:var(--g-pale);"></div>
  </div>`;
}

function triCountLabel(real, ar, ns, closed){
  const parts = [`${real} real.`];
  if (!closed) parts.push(`${ar} a real.`);
  parts.push(`${ns} no-show`);
  return parts.map((p, i) => `<span class="seg">${i > 0 ? '| ' : ''}${p}</span>`).join(' ');
}

function rowsHtml(list, closed){
  return list.map(([name, real, ar, ns]) => {
    const total = real + ar + ns;
    return `<div class="ch-row"><span class="name">${name}</span>${segBar(real, ar, ns)}<span class="ch-count">${total} (${triCountLabel(real, ar, ns, closed)})</span></div>`;
  }).join('');
}

const STATUS_COLOR = { green: '#0ED555', amber: '#e0a838', red: '#c0392b' };

function heroStatus(m){
  if (m.closed) {
    const ratio = m.prevendasReal / m.meta;
    return { st: statusOf(ratio), text: `${statusOf(ratio).label} ${Math.round(ratio * 100)}% da meta` };
  }
  const expected = m.expected || 0;
  const ratio = expected > 0 ? (m.prevendasReal / expected) : (m.prevendasReal === 0 ? 1 : 2);
  const st = statusOf(ratio);
  return { st, text: `${st.label} ${Math.round(ratio * 100)}% do MTD (${Math.round(expected)} agendamentos)` };
}

function stripHtml(m){
  if (m.closed) return '';
  const proj = m.prevendasReal + m.pvArealizar;
  const faltam = Math.max(0, m.meta - proj);
  const right = proj >= m.meta
    ? '<div class="s-covered">Meta coberta pelo agendado</div>'
    : `<div class="s-items"><div>👨‍💻 Faltam <b>${faltam} call${faltam === 1 ? '' : 's'}</b> para agendar</div><div>📅 Restam <b>${m.diasUteisRestantes} dia${m.diasUteisRestantes === 1 ? '' : 's'} úteis</b> no mês</div></div>`;
  return `<div class="card strip">
    <div><p class="s-label">Projeção do mês</p><p class="s-val">${proj} de ${m.meta}</p><p class="s-sub">${m.prevendasReal} realizadas + ${m.pvArealizar} a realizar</p></div>
    ${right}
  </div>`;
}

function heroChartHtml(m, color){
  if (!m.dataDisponivel) return '<div class="chart-wrap"><p class="week-empty">dado indisponível</p></div>';
  const { bdays, dec, cumReal, cumProj } = m.chart;
  const n = bdays.length, META = m.meta;
  const W = 560, H = 215, L = 30, R = 12, T = 12, B = 26;
  const projTotal = m.prevendasReal + m.pvArealizar;
  const top = Math.max(META, m.closed ? m.prevendasReal : projTotal);
  const stepY = top > 25 ? 10 : 5;
  const yMax = Math.max(5, Math.ceil(top / stepY) * stepY);
  const x = i => L + (n > 1 ? i * (W - L - R) / (n - 1) : (W - L - R) / 2);
  const y = v => T + (H - T - B) * (1 - v / yMax);

  let g = '';
  for (let v = 0; v <= yMax; v += stepY) {
    g += `<line x1="${L}" y1="${y(v)}" x2="${W - R}" y2="${y(v)}" stroke="var(--border)" stroke-opacity="0.6" stroke-width="1"/>`;
    g += `<text x="${L - 6}" y="${y(v) + 3}" font-size="9" fill="var(--text-muted)" text-anchor="end">${v}</text>`;
  }
  [0, Math.floor((n - 1) / 2), n - 1].forEach(i => {
    g += `<text x="${x(i)}" y="${H - 8}" font-size="9.5" fill="var(--text-secondary)" text-anchor="middle">${ddmm(bdays[i])}</text>`;
  });
  g += `<polyline points="${bdays.map((d, i) => `${x(i)},${y(META * (i + 1) / n)}`).join(' ')}" fill="none" stroke="#c9c8bf" stroke-width="1.3"/>`;

  if (!m.closed) {
    const pts = [];
    for (let i = Math.max(dec - 1, 0); i < n; i++) pts.push(`${x(i)},${y(cumProj[i])}`);
    g += `<polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="1.5" stroke-dasharray="4 3" opacity=".6"/>`;
    g += `<circle cx="${x(n - 1)}" cy="${y(cumProj[n - 1])}" r="2.4" fill="#fff" stroke="${color}" stroke-width="1.4"/>`;
  }
  if (dec > 0) {
    const pts = [];
    for (let i = 0; i < dec; i++) pts.push(`${x(i)},${y(cumReal[i])}`);
    g += `<polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="1.7"/>`;
    for (let i = 0; i < dec; i++) g += `<circle cx="${x(i)}" cy="${y(cumReal[i])}" r="2.2" fill="${color}"/>`;
  }
  const step = n > 1 ? (W - L - R) / (n - 1) : (W - L - R);
  for (let i = 0; i < n; i++) {
    const metaV = (META * (i + 1) / n).toFixed(1).replace('.', ',');
    const tip = i < dec
      ? `${ddmm(bdays[i])} · Realizado ${cumReal[i]} · Meta ${metaV}`
      : `${ddmm(bdays[i])}${bdays[i] === m.hojeIso ? ' (hoje)' : ''} · Projeção ${cumProj[i]} · Meta ${metaV}`;
    g += `<rect x="${x(i) - step / 2}" y="${T}" width="${step}" height="${H - T - B}" fill="transparent" data-tip="${tip}"/>`;
  }
  const legend = `<div class="legend">
    <span><span class="line-swatch" style="background:${color};"></span>Realizado</span>
    ${m.closed ? '' : `<span><span class="line-swatch dashed" style="border-top-color:${color}; opacity:.7;"></span>Projeção</span>`}
    <span><span class="line-swatch" style="background:#c9c8bf;"></span>Meta de agendamentos = ${META}</span>
  </div>`;
  return `<div class="chart-wrap"><svg viewBox="0 0 ${W} ${H}" width="100%">${g}</svg>${legend}</div>`;
}

function heroHtml(m){
  const { st, text } = heroStatus(m);
  return `<div class="card hero">
    <div class="hero-left">
      <p class="hero-label">Agendamentos realizados com envolvimento de pré-vendas</p>
      <p class="hero-num">${m.prevendasReal}</p>
      <span class="badge badge-${st.css}">${text}</span>
      <p class="meta-line">🎯 Meta = ${m.meta} agendamentos</p>
    </div>
    ${heroChartHtml(m, STATUS_COLOR[st.css])}
  </div>`;
}

function realizadosSubtext(real, ns, ar){
  let s = `${real} realizados · ${ns} no-shows`;
  if (ar > 0) s += ` · +${ar} a realizar`;
  return s;
}

function cardsHtml(m){
  const mc = (title, v, sub) => `<div class="card metric-card"><p class="label">${title}</p><div class="value-row"><p class="value">${v}</p></div>${sub ? `<p class="sub">${sub}</p>` : ''}</div>`;
  const cards = [];
  if (m.scope === 'pv') {
    if (!m.closed) {
      cards.push(mc('Agendamentos ainda à realizar no mês', m.pvArealizar));
      cards.push(mc(`Agendamentos previstos para acontecer hoje (${ddmm(m.hojeIso)})`, m.pvHoje));
    }
    const p = m.ns.pv;
    cards.push(`<div class="card metric-card"><p class="label">No-show (meta 10%)</p><div class="value-row"><div class="vline"><span class="value${p > 10 ? ' red' : ''}">${p}%</span><span class="vs">(${m.pvNsCount} de ${m.pvRealizadasCount} agendamentos realizados)</span></div></div></div>`);
  } else {
    if (!m.closed) cards.push(mc('Agendamentos à realizar no mês', m.propriaAr + m.externaAr, `${m.propriaAr} canais próprios · ${m.externaAr} externos`));
    cards.push(`<div class="card metric-card"><p class="label">No-show (meta 10%)</p><div class="twin">
      <div><p class="value${m.ns.total > 10 ? ' red' : ''}">${m.ns.total}%</p><p class="sub">total</p></div>
      <div><p class="value${m.ns.pv > 10 ? ' red' : ''}">${m.ns.pv}%</p><p class="sub">pré-vendas</p></div></div></div>`);
    cards.push(mc('Total de agendamentos (canais próprios)', m.propriaRealTotal + m.propriaNs + m.propriaAr, realizadosSubtext(m.propriaRealTotal, m.propriaNs, m.propriaAr)));
    cards.push(mc('Total de agendamentos (canais próprios + externos)', m.totalReal + m.totalNs + m.totalAr, realizadosSubtext(m.totalReal, m.totalNs, m.totalAr)));
  }
  return `<div class="summary-grid" style="--cols:${cards.length}">${cards.join('')}</div>`;
}

function phoneCell(r){
  if (r.pid) return `<a class="plink" href="https://investai.pipedrive.com/deal/${r.pid}" target="_blank" rel="noopener">Abrir ↗</a>`;
  return '<span class="plink off" title="Sem pipedriveId nesta call — associe com: cli.py pipedrive">sem ID</span>';
}

function simpleTable(rows, empty){
  if (!rows.length) return `<p class="week-empty">${empty}</p>`;
  const body = rows.map(r => `<tr><td>${r.data}</td><td>${r.empresa}</td><td>${phoneCell(r)}</td></tr>`).join('');
  return `<div class="calls-table-scroll"><table class="calls-table"><thead><tr><th>Data</th><th>Empresa</th><th>Telefone</th></tr></thead><tbody>${body}</tbody></table></div>`;
}

function actionTablesHtml(m){
  return `<div class="two-col">
    <div class="card week-card"><p class="title">No-shows do mês a reagendar · ${m.pendentes.length} pendentes</p>${simpleTable(m.pendentes, 'Nenhum no-show pendente de reagendamento.')}</div>
    <div class="card week-card"><p class="title">Calls de hoje (${ddmm(m.hojeIso)}) para enviar confirmação · ${m.hoje.length} calls</p>${simpleTable(m.hoje, 'Nenhuma call agendada pra hoje.')}</div>
  </div>`;
}

function callsTable(rows, mode, scope){
  const withPessoa = scope !== 'pv';
  const cols = 5 + (withPessoa ? 1 : 0);
  const body = rows.map(r => {
    const dateCell = mode === 'pipeline' && r.hoje ? `${r.data} <span class="today-tag">HOJE</span>` : r.data;
    let tag = '';
    if (mode === 'closed' && r.noShow) {
      tag = r.resched
        ? `<span class="nsre-tag" title="Reagendada p/ ${ddmm(r.resched)}">NO-SHOW REAGENDADO</span>`
        : '<span class="ns-tag">NO-SHOW</span>';
    }
    const pessoaCell = r.presales ? `${r.pessoa} <span class="badge-presales">PRÉ-VENDAS</span>` : r.pessoa;
    return `<tr><td>${dateCell}</td><td>${r.empresa}</td><td>${r.origem}</td><td>${r.canal}</td>${withPessoa ? `<td>${pessoaCell}</td>` : ''}<td>${tag}</td></tr>`;
  }).join('');
  return `<div class="calls-table-scroll">
    <table class="calls-table">
      <thead><tr><th>Data</th><th>Empresa</th><th>Origem</th><th>Canal</th>${withPessoa ? '<th>Agendada por</th>' : ''}<th></th></tr></thead>
      <tbody>${body || `<tr><td colspan="${cols}" class="week-empty">nenhuma call</td></tr>`}</tbody>
    </table>
  </div>`;
}

function toggleMonthDropdown(){
  document.getElementById('month-dropdown-list').hidden = !document.getElementById('month-dropdown-list').hidden;
}

function selectMonth(key){
  document.getElementById('month-dropdown-list').hidden = true;
  renderMonth(key);
}

document.addEventListener('click', e => {
  const dd = document.getElementById('month-dropdown');
  const list = document.getElementById('month-dropdown-list');
  if (dd && list && !list.hidden && !dd.contains(e.target)) list.hidden = true;
});

function renderMonth(key){
  ACTIVE_MES = key;
  const m = VIEWS[key];
  document.getElementById('month-dropdown-label').textContent = m.label;
  document.querySelectorAll('.month-dropdown-item').forEach(el => el.classList.toggle('active', el.dataset.mes === key));
  document.getElementById('m-mtdline').textContent = m.mtdLine;
  document.getElementById('m-strip').innerHTML = stripHtml(m);
  document.getElementById('m-hero').innerHTML = heroHtml(m);
  document.getElementById('m-cards').innerHTML = cardsHtml(m);

  document.getElementById('m-origem-legend').style.display = m.origemDisponivel ? '' : 'none';
  if (m.origemDisponivel) {
    let origemHtml = '';
    Object.keys(m.origem).forEach(section => {
      if (m.scope === 'pv' && !m.origem[section].length) return;
      origemHtml += `<p class="seg-section-label">${section}</p>${rowsHtml(m.origem[section], m.closed)}`;
    });
    document.getElementById('m-origem').innerHTML = origemHtml || '<p class="week-empty">Sem calls neste recorte.</p>';
  } else {
    document.getElementById('m-origem').innerHTML = '<p class="week-empty">dado indisponível</p>';
  }
  document.getElementById('m-canal-legend').style.display = m.canalDisponivel ? '' : 'none';
  document.getElementById('m-canal').innerHTML = m.canalDisponivel
    ? (rowsHtml(m.canal, m.closed) || '<p class="week-empty">Sem calls neste recorte.</p>')
    : '<p class="week-empty">dado indisponível</p>';

  const pv = m.scope === 'pv';
  document.getElementById('m-actions').innerHTML = pv && !m.closed ? actionTablesHtml(m) : '';
  document.getElementById('m-people-card').hidden = pv;

  const realizedCard = document.getElementById('m-realized-card');
  if (m.closed) {
    document.getElementById('m-week-title').textContent = m.allTitle;
    document.getElementById('m-week-body').innerHTML = callsTable(m.allCalls, 'closed', m.scope);
    realizedCard.hidden = true;
  } else {
    document.getElementById('m-week-title').textContent = m.week.title;
    document.getElementById('m-week-body').innerHTML = callsTable(m.week.calls, 'pipeline', m.scope);
    document.getElementById('m-realized-title').textContent = m.realized.title;
    document.getElementById('m-realized-body').innerHTML = callsTable(m.realized.calls, 'closed', m.scope);
    realizedCard.hidden = false;
  }

  const maxP = Math.max(...m.pessoa.map(p => p[1] + p[2] + p[3]), 1);
  document.getElementById('m-pessoa').innerHTML = m.pessoa.map(([name, real, ar, ns]) => {
    const total = real + ar + ns;
    return `<div class="p-row">
      <span class="name">${name}</span>
      <div class="p-track">
        <div style="width:${real/maxP*100}%; background:var(--g-dark);"></div>
        <div style="width:${ar/maxP*100}%; background:var(--g-mid);"></div>
        <div style="width:${ns/maxP*100}%; background:var(--g-pale);"></div>
      </div>
      <span class="p-count">${total} (${triCountLabel(real, ar, ns, m.closed)})</span>
    </div>`;
  }).join('');
}

function setScope(s){
  SCOPE = s;
  document.querySelectorAll('#scope button').forEach(b => b.classList.toggle('on', b.dataset.s === s));
  recomputeViews();
  if (ACTIVE_MES) renderMonth(ACTIVE_MES);
  if (ACTIVE_TAB === 'historico') renderHistorico();
}

function switchTab(tab){
  ACTIVE_TAB = tab;
  document.getElementById('view-mensal').style.display = tab === 'mensal' ? 'block' : 'none';
  document.getElementById('view-historico').style.display = tab === 'historico' ? 'block' : 'none';
  document.getElementById('month-dropdown').style.display = tab === 'mensal' ? '' : 'none';
  if (tab !== 'mensal') document.getElementById('month-dropdown-list').hidden = true;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  if (tab === 'historico') renderHistorico();
}

function xPositions(n, xStart, xEnd){
  if (n === 1) return [(xStart + xEnd) / 2];
  const step = (xEnd - xStart) / (n - 1);
  return Array.from({length:n}, (_, i) => xStart + i * step);
}

function monthTick(m){
  return `${m.label.split(' ')[0].slice(0,3)}/${m.label.slice(-2)}`;
}

const CHART_LEFT = 64, CHART_RIGHT = 650, CHART_TOP = 20, CHART_BOTTOM = 150;
const SERIES_COLORS = ['#3f7a5c','#6b46c1','#c0392b','#c9862a','#2d6f8e','#8a5a3f','#a3335c','#4f7ca8','#5c8a3f','#8a3f7a'];

function niceMax(values, floor){
  const max = Math.max(...values, floor || 0);
  return max <= 0 ? (floor || 1) : max * 1.15;
}

function yTicks(maxVal, count){
  count = count || 4;
  return Array.from({length: count}, (_, i) => {
    const value = maxVal * i / (count - 1);
    const y = CHART_BOTTOM - (value / maxVal) * (CHART_BOTTOM - CHART_TOP);
    return { value, y };
  });
}

function axisSvg(ticks, fmt){
  return ticks.map(t => `
    <line x1="${CHART_LEFT}" y1="${t.y}" x2="${CHART_RIGHT}" y2="${t.y}" stroke="var(--border)" stroke-opacity="0.6" stroke-width="1"/>
    <text x="${CHART_LEFT-8}" y="${t.y+3}" font-size="9" fill="var(--text-muted)" text-anchor="end">${fmt(t.value)}</text>
  `).join('');
}

function refLineSvg(y, color){
  return `<line x1="${CHART_LEFT}" y1="${y}" x2="${CHART_RIGHT}" y2="${y}" stroke="${color}" stroke-dasharray="4,4" stroke-width="1" opacity="0.7"/>`;
}

function lineChartSvg({ months, series, maxVal, fmtVal, refLine, openMonthMarker }){
  const xs = xPositions(months.length, CHART_LEFT+24, CHART_RIGHT-24);
  const yFor = v => CHART_BOTTOM - (v/maxVal) * (CHART_BOTTOM - CHART_TOP);
  const n = months.length;
  // Projeção é por mês (closed), não "o último item da lista" — com dado de
  // mês futuro salvo adiantado, o mês corrente pode não ser mais o último
  // ponto do eixo, e mais de um mês pode estar aberto ao mesmo tempo
  // (seção 10 do CLAUDE.md).
  const isProjected = i => !!openMonthMarker && !months[i].closed;
  let svg = `<svg viewBox="0 0 720 200" width="100%">`;
  svg += axisSvg(yTicks(maxVal), fmtVal);
  svg += `<line x1="${CHART_LEFT}" y1="${CHART_BOTTOM}" x2="${CHART_RIGHT}" y2="${CHART_BOTTOM}" stroke="var(--border)"/>`;
  if (refLine) svg += refLineSvg(yFor(refLine.value), refLine.color);
  series.forEach(s => {
    const vals = months.map(m => s.getValue(m));
    for (let i = 1; i < n; i++) {
      const dashed = isProjected(i);
      svg += `<line x1="${xs[i-1]}" y1="${yFor(vals[i-1])}" x2="${xs[i]}" y2="${yFor(vals[i])}" stroke="${s.color}" stroke-width="1.5"${dashed ? ' stroke-dasharray="4,3"' : ''}/>`;
    }
    svg += months.map((m,i) => {
      const v = vals[i];
      const proj = isProjected(i) ? ' (projeção)' : '';
      return `<circle cx="${xs[i]}" cy="${yFor(v)}" r="2.5" fill="${s.color}" data-tip="${s.name} · ${monthTick(m)}${proj}: ${fmtVal(v)}"/>`;
    }).join('');
  });
  svg += months.map((m,i) => `<text x="${xs[i]}" y="${CHART_BOTTOM+18}" font-size="10" fill="var(--text-secondary)" text-anchor="middle">${monthTick(m)}${isProjected(i)?'*':''}</text>`).join('');
  svg += `</svg>`;
  return svg;
}

function barChartSvg({ months, meta, soloPv }){
  const usable = CHART_RIGHT - CHART_LEFT - 48;
  const slot = Math.min(110, Math.max(50, usable / months.length));
  const totalWidth = slot * months.length;
  const startX = CHART_LEFT + 24 + (usable - totalWidth) / 2 + slot / 2;
  const xs = months.map((_, i) => startX + i * slot);
  const barW = Math.min(48, slot * 0.55);
  const maxVal = niceMax(months.map(m => soloPv ? m.presalesRealTotal + m.pvArealizar : m.totalReal + m.totalAr), meta);
  const yFor = v => CHART_BOTTOM - (v/maxVal) * (CHART_BOTTOM - CHART_TOP);

  let svg = `<svg viewBox="0 0 720 200" width="100%">`;
  svg += axisSvg(yTicks(maxVal), v => Math.round(v));
  svg += `<line x1="${CHART_LEFT}" y1="${CHART_BOTTOM}" x2="${CHART_RIGHT}" y2="${CHART_BOTTOM}" stroke="var(--border)"/>`;
  svg += refLineSvg(yFor(meta), '#a9a89f');
  months.forEach((m, i) => {
    // mês aberto projeta: realizado + a realizar (mês fechado tem ar=0, então não muda nada).
    const pv = m.presalesRealTotal + m.pvArealizar;
    const total = m.totalReal + m.totalAr;
    const outros = total - pv;
    const proj = m.closed ? '' : ' (projeção)';
    const x = xs[i] - barW/2;
    const hPv = CHART_BOTTOM - yFor(pv);
    const hOut = (CHART_BOTTOM - yFor(pv + outros)) - hPv;
    svg += `<rect x="${x}" y="${CHART_BOTTOM-hPv}" width="${barW}" height="${hPv}" fill="var(--g-dark)" data-tip="${monthTick(m)} · agendado pela pré-vendas${proj}: ${pv}"/>`;
    if (!soloPv) svg += `<rect x="${x}" y="${CHART_BOTTOM-hPv-hOut}" width="${barW}" height="${hOut}" fill="var(--g-pale)" data-tip="${monthTick(m)} · sem envolvimento de pré-vendas${proj}: ${outros}"/>`;
    svg += `<text x="${xs[i]}" y="${CHART_BOTTOM+18}" font-size="10" fill="var(--text-secondary)" text-anchor="middle">${monthTick(m)}${m.closed?'':'*'}</text>`;
  });
  svg += `</svg>`;
  return svg;
}

function rowProjected(r){
  return r[1] + r[2]; // realizada + a_realizar (projeção do mês corrente; mês fechado tem ar=0)
}

function seriesFromRows(months, getRows){
  const names = new Set();
  months.forEach(m => getRows(m).forEach(r => { if (rowProjected(r) > 0) names.add(r[0]); }));
  return [...names];
}

function renderSeriesChart(containerId, legendId, months, getRows){
  const names = seriesFromRows(months, getRows);
  if (!names.length) {
    document.getElementById(containerId).innerHTML = '<p class="week-empty">sem dados no período</p>';
    document.getElementById(legendId).innerHTML = '';
    return;
  }
  const maxVal = niceMax(months.flatMap(m => getRows(m).map(rowProjected)), 1);
  const series = names.map((name, i) => ({
    name, color: SERIES_COLORS[i % SERIES_COLORS.length],
    getValue: m => rowProjected(getRows(m).find(r => r[0] === name) || [name,0,0,0]),
  }));
  document.getElementById(containerId).innerHTML = lineChartSvg({ months, series, maxVal, fmtVal: v => Math.round(v), openMonthMarker: true });
  document.getElementById(legendId).innerHTML = series.map(s =>
    `<span><span class="line-swatch" style="background:${s.color};"></span>${s.name}</span>`
  ).join('');
}

function initTooltips(){
  const tip = document.getElementById('chart-tip');
  document.body.addEventListener('mousemove', e => {
    const target = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (target) {
      tip.textContent = target.getAttribute('data-tip');
      tip.style.left = e.clientX + 'px';
      tip.style.top = e.clientY + 'px';
      tip.hidden = false;
    } else {
      tip.hidden = true;
    }
  });
}

function renderHistorico(){
  if (!HIST_ORDER.length) {
    ['chart-noshow','chart-meta','chart-origem','chart-canal','chart-pessoa'].forEach(id =>
      document.getElementById(id).innerHTML = '<p class="week-empty">sem meses salvos ainda</p>'
    );
    return;
  }
  const months = HIST_ORDER.map(k => VIEWS[k]);

  const pvOnly = SCOPE === 'pv';
  document.getElementById('leg-ns-total').style.display = pvOnly ? 'none' : '';
  document.getElementById('leg-sem-pv').style.display = pvOnly ? 'none' : '';
  document.getElementById('hist-pessoa-card').hidden = pvOnly;
  const maxNs = niceMax(months.flatMap(m => pvOnly ? [m.ns.pv] : [m.ns.total, m.ns.pv]), 10);
  document.getElementById('chart-noshow').innerHTML = lineChartSvg({
    months, maxVal: maxNs, fmtVal: v => `${Math.round(v)}%`,
    refLine: { value: 10, color: '#c9a29c' },
    series: [
      ...(pvOnly ? [] : [{ name: 'No-show total', color: 'var(--text-secondary)', getValue: m => m.ns.total }]),
      { name: 'No-show pré-vendas', color: 'var(--g-dark)', getValue: m => m.ns.pv },
    ],
  });

  document.getElementById('chart-meta').innerHTML = barChartSvg({ months, meta: months[0].meta, soloPv: pvOnly });
  document.getElementById('chart-meta-goal-legend').textContent = `meta de agendamentos: ${months[0].meta}`;

  const origemRows = m => [...m.origem["CANAIS PRÓPRIOS"], ...m.origem["CANAIS EXTERNOS"]];
  const monthsOrigem = months.filter(m => m.origemDisponivel);
  const monthsCanal = months.filter(m => m.canalDisponivel);
  renderSeriesChart('chart-origem', 'chart-origem-legend', monthsOrigem, origemRows);
  renderSeriesChart('chart-canal', 'chart-canal-legend', monthsCanal, m => m.canal);
  if (!pvOnly) renderSeriesChart('chart-pessoa', 'chart-pessoa-legend', months, m => m.pessoa);
}
'''
