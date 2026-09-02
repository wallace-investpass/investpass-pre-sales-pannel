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
    default_mes = payload["defaultMes"]

    options_html = ""
    for key in payload["allKeys"]:
        label = payload["months"][key]["label"]
        selected = " selected" if key == default_mes else ""
        options_html += f'<option value="{key}"{selected}>{label}</option>'

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
    <select id="month-filter" onchange="renderMonth(this.value)">
      {options_html}
    </select>
  </div>

  <div id="view-mensal">
    <div class="header-row">
      <span class="mtd-line" id="m-mtdline"></span>
    </div>

    <div class="card">
      <div class="hero-top">
        <div>
          <p class="hero-label">Agendamentos realizados com envolvimento de pré-vendas</p>
          <div class="hero-number">
            <span class="big" id="m-hero-big"></span>
            <span class="badge" id="m-badge"></span>
          </div>
        </div>
        <div class="proj-box" id="m-proj-box">
          <p class="p-label" id="m-proj-label">Projeção final do mês</p>
          <p class="p-value" id="m-proj-value"></p>
          <p class="p-sub" id="m-proj-sub"></p>
        </div>
      </div>
      <div class="bar-outer">
        <div class="bar-fill" id="m-bar-fill"></div>
        <div class="bar-fill-ar" id="m-bar-fill-ar"></div>
        <div class="bar-marker" id="m-bar-marker"><span class="m-label" id="m-bar-marker-label"></span></div>
      </div>
    </div>

    <div class="summary-grid" id="m-summary-grid">
      <div class="card metric-card" id="m-card-ar-wrap"><p class="label">À realizar no mês</p><p class="value" id="m-card-ar"></p><p class="sub" id="m-card-ar-sub"></p></div>
      <div class="card metric-card">
        <p class="label">No-show (meta 10%)</p>
        <div class="twin">
          <div><p class="value" id="m-ns-total"></p><p class="sub">total</p></div>
          <div><p class="value" id="m-ns-pv"></p><p class="sub">pré-vendas</p></div>
        </div>
      </div>
      <div class="card metric-card"><p class="label">Canais próprios</p><p class="value" id="m-card-propria"></p><p class="sub" id="m-card-propria-sub"></p></div>
      <div class="card metric-card"><p class="label">Total de agendamentos (canais próprios + externos)</p><p class="value" id="m-card-total"></p><p class="sub" id="m-card-total-sub"></p></div>
    </div>

    <div class="seg-grid">
      <div class="card seg-card">
        <p class="title">🌱 Origem do lead</p>
        <div id="m-origem"></div>
        <div class="p-legend">
          <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
          <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
          <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
        </div>
      </div>
      <div class="card seg-card">
        <p class="title">📲 Canal de agendamento</p>
        <div id="m-canal"></div>
        <div class="p-legend">
          <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
          <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
          <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
        </div>
      </div>
    </div>

    <div class="card week-card"><p class="title" id="m-week-title"></p><div id="m-week-body"></div></div>

    <div class="card people-card">
      <p class="title">Por pessoa</p>
      <div id="m-pessoa"></div>
      <div class="p-legend">
        <span><span class="dot" style="background:var(--g-dark);"></span>realizadas</span>
        <span><span class="dot" style="background:var(--g-mid);"></span>a realizar</span>
        <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>no-show</span>
      </div>
    </div>
  </div>

  <div id="view-historico">
    <div class="card hist-card">
      <p class="title">Taxa de no-show MoM</p>
      <div id="chart-noshow"></div>
      <div class="legend">
        <span><span class="line-swatch" style="background:var(--text-secondary);"></span>No-show total</span>
        <span><span class="line-swatch" style="background:var(--g-dark);"></span>No-show pré-vendas</span>
      </div>
    </div>
    <div class="card hist-card">
      <p class="title">Performance de pré-vendas MoM</p>
      <div id="chart-meta"></div>
      <div class="legend">
        <span><span class="dot" style="background:var(--g-dark);"></span>Agendado pela pré-vendas</span>
        <span><span class="dot" style="background:var(--g-pale); border:0.5px solid var(--border);"></span>Sem envolvimento de pré-vendas</span>
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
    <div class="card hist-card">
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
const DEFAULT_MES = {json.dumps(default_mes)};

{JS}

if (DEFAULT_MES) {{ renderMonth(DEFAULT_MES); }}
initTooltips();
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
  select#month-filter { height:32px; border-radius:8px; border:0.5px solid var(--border); background:var(--surface-1); padding:0 10px; font-size:13px; font-family:'Montserrat',sans-serif; }

  .header-row { display:flex; align-items:baseline; justify-content:flex-end; margin-bottom:16px; flex-wrap:wrap; gap:6px; }
  .header-row .mtd-line { font-size:12px; color:var(--text-muted); }

  .card { background:var(--surface-1); border:0.5px solid var(--border); border-radius:12px; padding:18px 20px; margin-bottom:14px; }
  .hero-top { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap; }
  .hero-label { font-size:11.5px; font-weight:600; color:var(--text-secondary); letter-spacing:0.02em; text-transform:uppercase; margin:0 0 6px; }
  .hero-number { display:flex; align-items:baseline; gap:10px; }
  .hero-number .big { font-size:42px; font-weight:600; line-height:1; }
  .badge { padding:5px 12px; border-radius:8px; font-size:12.5px; font-weight:600; white-space:nowrap; }
  .badge-green { background:var(--green-bg); color:var(--green-text); }
  .badge-amber { background:var(--amber-bg); color:var(--amber); }
  .badge-red { background:var(--red-bg); color:var(--red); }
  .proj-box { background:var(--surface-0); border-radius:10px; padding:10px 14px; min-width:170px; border:0.5px solid transparent; }
  .proj-box .p-label { font-size:11px; color:var(--text-muted); margin:0 0 3px; }
  .proj-box .p-value { font-size:18px; font-weight:600; margin:0; }
  .proj-box .p-sub { font-size:11px; color:var(--text-muted); margin:3px 0 0; }
  .proj-box.proj-green { background:var(--green-bg); border-color:#bfe6cb; }
  .proj-box.proj-green .p-value { color:var(--green-text); }
  .proj-box.proj-amber { background:var(--amber-bg); border-color:#eecf9c; }
  .proj-box.proj-amber .p-value { color:var(--amber); }
  .proj-box.proj-red { background:var(--red-bg); border-color:#eeb8b0; }
  .proj-box.proj-red .p-value { color:var(--red); }
  .bar-outer { position:relative; height:14px; border-radius:7px; background:var(--surface-0); margin-top:40px; transition:box-shadow 150ms ease; }
  .bar-outer:hover { box-shadow:0 0 0 1px #d8d6cb, 0 4px 14px rgba(26,26,24,.08); }
  .bar-fill { position:absolute; left:0; top:0; height:100%; border-radius:7px 0 0 7px; }
  .bar-fill.bar-green { background:var(--brand-green); }
  .bar-fill.bar-amber { background:#e0a838; }
  .bar-fill.bar-red { background:var(--red); }
  .bar-fill-ar { position:absolute; top:0; height:100%; }
  .bar-fill-ar.bar-green { background:#a8ecc0; }
  .bar-fill-ar.bar-amber { background:#f3d99b; }
  .bar-fill-ar.bar-red { background:#f0b3ac; }
  .bar-marker { position:absolute; top:-9px; width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-top:9px solid var(--text-primary); transform:translateX(-6px); }
  .bar-marker .m-label { position:absolute; top:-24px; left:50%; transform:translateX(-50%); font-size:10px; font-weight:600; color:var(--text-secondary); white-space:nowrap; }

  .summary-grid { display:grid; gap:12px; margin-bottom:14px; grid-template-columns:repeat(4,1fr); }
  .summary-grid.cols-3 { grid-template-columns:repeat(3,1fr); }
  .card.metric-card { transition:box-shadow 150ms ease; }
  .card.metric-card:hover { box-shadow:0 0 0 1px #d8d6cb, 0 4px 14px rgba(26,26,24,.08); }
  .metric-card .label { font-size:12px; color:var(--text-secondary); margin:0 0 6px; font-weight:600; min-height:32px; display:flex; align-items:flex-end; }
  .metric-card .value { font-size:22px; font-weight:500; margin:0; }
  .metric-card .value.red { color:var(--red); }
  .metric-card .sub { font-size:11px; color:var(--text-muted); margin:6px 0 0; }
  .twin { display:flex; gap:18px; }

  .seg-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
  .seg-card .title { font-size:13px; color:var(--text-secondary); margin:0 0 10px; font-weight:600; }
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
    .summary-grid, .summary-grid.cols-3 { grid-template-columns:1fr 1fr; }
    .seg-grid { grid-template-columns:1fr; }
  }
'''

JS = r'''
function statusOf(ratio){
  if (ratio > 0.9) return { css: 'green', label: '🟢' };
  if (ratio >= 0.7) return { css: 'amber', label: '🟡' };
  return { css: 'red', label: '🔴' };
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
  if (closed) {
    return `<span class="seg">${real}·NS ${ns}</span>`;
  }
  return `<span class="seg">${real} real.</span> <span class="seg">| ${ar} a real.</span> <span class="seg">| ${ns} no-show</span>`;
}

function rowsHtml(list, closed){
  return list.map(([name, real, ar, ns]) => {
    const total = real + ar + ns;
    return `<div class="ch-row"><span class="name">${name}</span>${segBar(real, ar, ns)}<span class="ch-count">${total} (${triCountLabel(real, ar, ns, closed)})</span></div>`;
  }).join('');
}

function callsTable(rows, withNoShow){
  const body = rows.map(r => {
    const [d, empresa, origem, canal, pessoa, ns] = r;
    return `<tr>
      <td>${d}</td><td>${empresa}</td><td>${origem}</td><td>${canal}</td><td>${pessoa}</td>
      <td>${ns ? '<span class="ns-tag">NO-SHOW</span>' : ''}</td>
    </tr>`;
  }).join('');
  return `<div class="calls-table-scroll">
    <table class="calls-table">
      <thead><tr><th>Data</th><th>Empresa</th><th>Origem</th><th>Canal</th><th>Agendada por</th><th></th></tr></thead>
      <tbody>${body || '<tr><td colspan="6" class="week-empty">nenhuma call</td></tr>'}</tbody>
    </table>
  </div>`;
}

function renderMonth(key){
  const m = MONTHS[key];
  document.getElementById('month-filter').value = key;
  document.getElementById('m-mtdline').textContent = m.mtdLine;
  document.getElementById('m-hero-big').textContent = m.prevendasReal;

  const badge = document.getElementById('m-badge');
  const projBox = document.getElementById('m-proj-box');
  let st, expectedForMarker;
  if (m.closed) {
    const pct = Math.round((m.prevendasReal / m.meta) * 100);
    st = statusOf(m.prevendasReal / m.meta);
    badge.textContent = `${st.label} ${pct}% da meta`;
  } else {
    const expected = m.expected || 0;
    expectedForMarker = expected;
    const ratio = expected > 0 ? (m.prevendasReal / expected) : (m.prevendasReal === 0 ? 1 : 2);
    const pct = Math.round(ratio * 100);
    st = statusOf(ratio);
    badge.textContent = `${st.label} ${pct}% do MTD (${Math.round(expected)} agendamentos)`;
  }
  badge.className = 'badge badge-' + st.css;
  projBox.className = 'proj-box proj-' + st.css;

  document.getElementById('m-proj-label').textContent = m.closed ? 'Fechamento do mês' : 'Projeção final do mês';
  document.getElementById('m-proj-value').textContent = `${m.prevendasReal + m.pvArealizar} de ${m.meta}`;
  document.getElementById('m-proj-sub').textContent = m.closed ? '' : `${m.prevendasReal} realizadas + ${m.pvArealizar} a realizar`;

  const barPct = Math.min(100, (m.prevendasReal / m.meta) * 100);
  const barFillEl = document.getElementById('m-bar-fill');
  barFillEl.style.width = barPct + '%';
  barFillEl.className = 'bar-fill bar-' + st.css;
  barFillEl.setAttribute('data-tip', `${m.prevendasReal} realizadas`);
  const barArEl = document.getElementById('m-bar-fill-ar');
  barArEl.className = 'bar-fill-ar bar-' + st.css;
  barArEl.setAttribute('data-tip', `${m.pvArealizar} a realizar`);
  if (m.closed || !m.pvArealizar) {
    barArEl.style.width = '0%';
  } else {
    const arPct = Math.min(100 - barPct, (m.pvArealizar / m.meta) * 100);
    barArEl.style.left = barPct + '%';
    barArEl.style.width = arPct + '%';
  }
  const marker = document.getElementById('m-bar-marker');
  if (m.closed) {
    marker.style.display = 'none';
  } else {
    marker.style.display = 'block';
    marker.style.left = `calc(${(expectedForMarker/m.meta)*100}% - 1px)`;
    document.getElementById('m-bar-marker-label').textContent = `MTD - ${Math.round(expectedForMarker)}`;
  }

  document.getElementById('m-card-propria').textContent = m.prevendasReal + m.outrosPropria;
  document.getElementById('m-card-propria-sub').textContent = `${m.prevendasReal} pela pré-vendas · ${m.outrosPropria} outros vendedores`;

  const grid = document.getElementById('m-summary-grid');
  const arWrap = document.getElementById('m-card-ar-wrap');
  if (m.closed) {
    arWrap.style.display = 'none';
    grid.classList.add('cols-3');
  } else {
    arWrap.style.display = '';
    grid.classList.remove('cols-3');
    const propriaAr = m.origem["CANAIS PRÓPRIOS"].reduce((s, r) => s + r[2], 0);
    const externaAr = m.origem["CANAIS EXTERNOS"].reduce((s, r) => s + r[2], 0);
    document.getElementById('m-card-ar').textContent = propriaAr + externaAr;
    document.getElementById('m-card-ar-sub').textContent = `${propriaAr} canais próprios · ${externaAr} externos`;
  }

  document.getElementById('m-ns-total').textContent = `${m.ns.total}%`;
  document.getElementById('m-ns-total').className = 'value' + (m.ns.total > 10 ? ' red' : '');
  document.getElementById('m-ns-pv').textContent = `${m.ns.pv}%`;
  document.getElementById('m-ns-pv').className = 'value' + (m.ns.pv > 10 ? ' red' : '');

  document.getElementById('m-card-total').textContent = m.totalReal + m.totalNs + m.totalAr;
  document.getElementById('m-card-total-sub').textContent = `${m.totalReal} realizados · ${m.totalNs} no-shows · +${m.totalAr} a realizar`;

  let origemHtml = '';
  Object.keys(m.origem).forEach(section => {
    origemHtml += `<p class="seg-section-label">${section}</p>${rowsHtml(m.origem[section], m.closed)}`;
  });
  document.getElementById('m-origem').innerHTML = origemHtml;
  document.getElementById('m-canal').innerHTML = rowsHtml(m.canal, m.closed);

  if (m.closed) {
    document.getElementById('m-week-title').textContent = `Todas as calls de ${m.label}`;
    document.getElementById('m-week-body').innerHTML = callsTable(m.allCalls, true);
  } else {
    document.getElementById('m-week-title').textContent = m.week.title;
    document.getElementById('m-week-body').innerHTML = callsTable(m.week.calls, false);
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
      <span class="p-count">${total} (${triCountLabel(real, ar, ns, false)})</span>
    </div>`;
  }).join('');
}

function switchTab(tab){
  document.getElementById('view-mensal').style.display = tab === 'mensal' ? 'block' : 'none';
  document.getElementById('view-historico').style.display = tab === 'historico' ? 'block' : 'none';
  document.getElementById('month-filter').style.display = tab === 'mensal' ? '' : 'none';
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

function refLineSvg(y, color, label){
  return `
    <line x1="${CHART_LEFT}" y1="${y}" x2="${CHART_RIGHT}" y2="${y}" stroke="${color}" stroke-dasharray="4,4" stroke-width="1" opacity="0.7"/>
    <text x="${CHART_LEFT+4}" y="${y-4}" font-size="9" fill="${color}">${label}</text>
  `;
}

function lineChartSvg({ months, series, maxVal, fmtVal, refLine }){
  const xs = xPositions(months.length, CHART_LEFT+24, CHART_RIGHT-24);
  const yFor = v => CHART_BOTTOM - (v/maxVal) * (CHART_BOTTOM - CHART_TOP);
  let svg = `<svg viewBox="0 0 720 200" width="100%">`;
  svg += axisSvg(yTicks(maxVal), fmtVal);
  svg += `<line x1="${CHART_LEFT}" y1="${CHART_BOTTOM}" x2="${CHART_RIGHT}" y2="${CHART_BOTTOM}" stroke="var(--border)"/>`;
  if (refLine) svg += refLineSvg(yFor(refLine.value), refLine.color, refLine.label);
  series.forEach(s => {
    const pts = months.map((m,i) => `${xs[i]},${yFor(s.getValue(m))}`).join(' ');
    svg += `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="1.5"/>`;
    svg += months.map((m,i) => {
      const v = s.getValue(m);
      return `<circle cx="${xs[i]}" cy="${yFor(v)}" r="2.5" fill="${s.color}" data-tip="${s.name} · ${monthTick(m)}: ${fmtVal(v)}"/>`;
    }).join('');
  });
  svg += months.map((m,i) => `<text x="${xs[i]}" y="${CHART_BOTTOM+18}" font-size="10" fill="var(--text-secondary)" text-anchor="middle">${monthTick(m)}</text>`).join('');
  svg += `</svg>`;
  return svg;
}

function barChartSvg({ months, meta }){
  const usable = CHART_RIGHT - CHART_LEFT - 48;
  const slot = Math.min(110, Math.max(50, usable / months.length));
  const totalWidth = slot * months.length;
  const startX = CHART_LEFT + 24 + (usable - totalWidth) / 2 + slot / 2;
  const xs = months.map((_, i) => startX + i * slot);
  const barW = Math.min(48, slot * 0.55);
  const maxVal = niceMax(months.map(m => m.totalReal), meta);
  const yFor = v => CHART_BOTTOM - (v/maxVal) * (CHART_BOTTOM - CHART_TOP);

  let svg = `<svg viewBox="0 0 720 200" width="100%">`;
  svg += axisSvg(yTicks(maxVal), v => Math.round(v));
  svg += `<line x1="${CHART_LEFT}" y1="${CHART_BOTTOM}" x2="${CHART_RIGHT}" y2="${CHART_BOTTOM}" stroke="var(--border)"/>`;
  svg += refLineSvg(yFor(meta), '#a9a89f', `meta de agendamentos = ${meta}`);
  months.forEach((m, i) => {
    const pv = m.presalesRealTotal;
    const outros = m.totalReal - pv;
    const x = xs[i] - barW/2;
    const hPv = CHART_BOTTOM - yFor(pv);
    const hOut = (CHART_BOTTOM - yFor(pv + outros)) - hPv;
    svg += `<rect x="${x}" y="${CHART_BOTTOM-hPv}" width="${barW}" height="${hPv}" fill="var(--g-dark)" data-tip="${monthTick(m)} · pré-vendas: ${pv}"/>`;
    svg += `<rect x="${x}" y="${CHART_BOTTOM-hPv-hOut}" width="${barW}" height="${hOut}" fill="var(--g-pale)" data-tip="${monthTick(m)} · resto: ${outros}"/>`;
    svg += `<text x="${xs[i]}" y="${CHART_BOTTOM+18}" font-size="10" fill="var(--text-secondary)" text-anchor="middle">${monthTick(m)}${m.closed?'':'*'}</text>`;
  });
  svg += `</svg>`;
  return svg;
}

function seriesFromRows(months, getRows){
  const names = new Set();
  months.forEach(m => getRows(m).forEach(r => { if (r[1] > 0) names.add(r[0]); }));
  return [...names];
}

function renderSeriesChart(containerId, legendId, months, getRows){
  const names = seriesFromRows(months, getRows);
  if (!names.length) {
    document.getElementById(containerId).innerHTML = '<p class="week-empty">sem dados no período</p>';
    document.getElementById(legendId).innerHTML = '';
    return;
  }
  const maxVal = niceMax(months.flatMap(m => getRows(m).map(r => r[1])), 1);
  const series = names.map((name, i) => ({
    name, color: SERIES_COLORS[i % SERIES_COLORS.length],
    getValue: m => (getRows(m).find(r => r[0] === name) || [name,0,0,0])[1],
  }));
  document.getElementById(containerId).innerHTML = lineChartSvg({ months, series, maxVal, fmtVal: v => Math.round(v) });
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
  const months = HIST_ORDER.map(k => MONTHS[k]);

  const maxNs = niceMax(months.flatMap(m => [m.ns.total, m.ns.pv]), 10);
  document.getElementById('chart-noshow').innerHTML = lineChartSvg({
    months, maxVal: maxNs, fmtVal: v => `${Math.round(v)}%`,
    refLine: { value: 10, color: '#c9a29c', label: 'meta de no-show: 10%' },
    series: [
      { name: 'No-show total', color: 'var(--text-secondary)', getValue: m => m.ns.total },
      { name: 'No-show pré-vendas', color: 'var(--g-dark)', getValue: m => m.ns.pv },
    ],
  });

  document.getElementById('chart-meta').innerHTML = barChartSvg({ months, meta: months[0].meta });

  const origemRows = m => [...m.origem["CANAIS PRÓPRIOS"], ...m.origem["CANAIS EXTERNOS"]];
  renderSeriesChart('chart-origem', 'chart-origem-legend', months, origemRows);
  renderSeriesChart('chart-canal', 'chart-canal-legend', months, m => m.canal);
  renderSeriesChart('chart-pessoa', 'chart-pessoa-legend', months, m => m.pessoa);
}
'''
