#!/usr/bin/env python3
"""Step 3 — generate the single self-contained results dashboard (HTML).

Reads outputs/step2_results.json (source of truth) and emits a polished,
offline, self-contained dashboard HTML file. All displayed numbers are computed
in the browser from the embedded JSON, so they always match the saved output.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "outputs", "step2_results.json")
OUT = os.path.join(ROOT, "dashboard_step3.html")

payload = json.load(open(SRC, encoding="utf-8"))
data_json = json.dumps(payload, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MBAX 6418 · Assignment 1 · Review Sentiment Results</title>
<style>
  :root{
    --bg:#f6f7f9; --surface:#ffffff; --border:#e6e8ee; --text:#1c2430;
    --muted:#5c6675; --accent:#2f6df6; --accent-ink:#ffffff;
    --pos:#1e8e5a; --neg:#d64545; --warn:#c77a12;
    --pos-bg:#e7f5ee; --neg-bg:#fcecea; --warn-bg:#fdf2e1;
    --radius:14px; --shadow:0 1px 2px rgba(16,24,40,.05),0 8px 24px -12px rgba(16,24,40,.12);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1040px;margin:0 auto;padding:40px 24px 72px}
  header{margin-bottom:28px}
  .eyebrow{font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
  h1{font-size:28px;line-height:1.2;margin:0 0 6px;letter-spacing:-.02em}
  .sub{color:var(--muted);margin:0;font-size:15px}
  .grid{display:grid;gap:16px}
  .grid.kpis{grid-template-columns:repeat(4,1fr)}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
    box-shadow:var(--shadow);padding:20px}
  .kpi .label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
  .kpi .value{font-size:34px;font-weight:750;letter-spacing:-.02em;margin-top:4px;font-variant-numeric:tabular-nums}
  .kpi .value small{font-size:16px;color:var(--muted);font-weight:600}
  .kpi .detail{font-size:13px;color:var(--muted);margin-top:2px}
  h2{font-size:18px;margin:0 0 4px;letter-spacing:-.01em}
  .lead{color:var(--muted);font-size:14px;margin:0 0 16px}
  .banner{border:1px solid var(--warn-bg);background:var(--warn-bg);border-left:5px solid var(--warn);
    border-radius:10px;padding:14px 16px;font-size:14px;color:#5a431a}
  .banner b{color:#3a2c0f}
  .bars{margin-top:10px}
  .bar-row{display:flex;align-items:center;gap:12px;margin:10px 0}
  .bar-row .bl{width:150px;flex:none;font-size:13px;color:var(--muted);text-align:right}
  .bar-row .btrack{flex:1;display:block;background:#e9edf4;border:1px solid #ccd3e0;border-radius:999px;height:22px;overflow:hidden}
  .bar-row .bfill{display:block;height:100%;width:0;border-radius:999px;min-width:4px;box-shadow:inset 0 -1px 0 rgba(0,0,0,.12)}
  .bar-row .bval{width:120px;flex:none;font-size:13px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums}
  .celltext.full .b{max-height:none;overflow:visible}
  .pos{color:var(--pos)} .neg{color:var(--neg)}
  .split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .donut{display:flex;align-items:center;gap:22px}
  .donut .ring{width:118px;height:118px;border-radius:50%;flex:none;
    background:conic-gradient(var(--pos) 0 var(--posdeg), var(--neg) var(--posdeg) 100%);
    display:flex;align-items:center;justify-content:center}
  .donut .ring .inner{width:76px;height:76px;border-radius:50%;background:var(--surface);
    display:flex;flex-direction:column;align-items:center;justify-content:center}
  .donut .ring .inner b{font-size:20px;font-weight:750}
  .donut .ring .inner span{font-size:11px;color:var(--muted)}
  .donut .ring .inner .sub2{font-size:10px;color:var(--muted)}
  .legend{font-size:13px;color:var(--muted)} .legend div{margin:4px 0}
  .legend .lt{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
  .legend .ms{margin-top:8px;border-top:1px solid var(--border);padding-top:8px;color:#9a5e00;font-size:12.5px}
  .dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:7px;vertical-align:-1px}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th{text-align:left;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
    padding:8px 10px;border-bottom:1px solid var(--border)}
  td{padding:10px;border-bottom:1px solid var(--border);vertical-align:top}
  tr:last-child td{border-bottom:0}
  .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap}
  .badge.pos{background:var(--pos-bg);color:var(--pos)} .badge.neg{background:var(--neg-bg);color:var(--neg)}
  .badge.ms{background:var(--warn-bg);color:#9a5e00;border:1px solid #e6c88a}
  .celltext{max-width:340px;color:#3a4350}
  .celltext .t{font-weight:600;color:var(--text)}
  .celltext .b{color:var(--muted);font-size:12.5px;display:block;margin-top:2px;max-height:3em;overflow:hidden}
  .foot{color:var(--muted);font-size:12px;margin-top:32px;line-height:1.6}
  .note{font-size:12px;color:var(--muted)}
  .filterbar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:16px;margin:14px 0;padding:14px;background:var(--bg);border:1px solid var(--border);border-radius:12px}
  .fgroup{display:flex;flex-direction:column;gap:6px}
  .fgroup.grow{flex:1;min-width:180px}
  .flabel{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
  .seg{display:flex;gap:4px;flex-wrap:wrap}
  .seg button{font:inherit;font-size:12.5px;font-weight:600;padding:6px 12px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--muted);cursor:pointer}
  .seg button:hover{border-color:var(--accent);color:var(--accent)}
  .seg button.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
  #kw{font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--text);min-width:160px}
  #kw:focus{outline:none;border-color:var(--accent)}
  .fcount{font-size:13px;color:var(--muted);align-self:center;white-space:nowrap}
  .fcount b{color:var(--text);font-size:15px}
  .reset{font:inherit;font-size:12.5px;font-weight:600;padding:7px 12px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--accent);cursor:pointer;white-space:nowrap}
  .reset:hover{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
  @media(max-width:760px){.grid.kpis{grid-template-columns:repeat(2,1fr)}.split{grid-template-columns:1fr}.bar-row .bl{width:110px}}
</style>
</head>
<body>
<script type="application/json" id="app-data">__DATA_JSON__</script>
<div class="wrap">
  <header>
    <p class="eyebrow">MBAX 6418 · Assignment 1 · Step 3 · Initial 100-Review Results</p>
    <h1>Amazon Gift Card Review Sentiment</h1>
    <p class="sub">How well an LLM classifies reviews as <b class="pos">POSITIVE</b> or <b class="neg">NEGATIVE</b>, checked against a label derived from the review's star rating.</p>
  </header>

  <section class="grid kpis" id="kpis"></section>

  <div class="banner" id="imbalanceBanner"></div>

  <section class="grid" style="margin-top:16px">
    <div class="card">
      <h2>Class imbalance &amp; where mistakes land</h2>
      <p class="lead">This batch is dominated by positive reviews. A model that guessed "positive" every time would score 93% — so the headline accuracy overstates real skill.</p>
      <div class="split">
        <div class="donut" id="donut"></div>
        <div id="imbalanceLegend" class="legend"></div>
      </div>
    </div>
    <div class="grid" style="gap:16px">
      <div class="card">
        <h2>Correct vs. incorrect</h2>
        <div class="bars" id="correctBar"></div>
      </div>
      <div class="card">
        <h2>Performance by class</h2>
        <div class="bars" id="classAcc"></div>
      </div>
    </div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Mismatched reviews <span class="note">(model disagreed with the rating-derived label)</span></h2>
    <p class="lead" id="mismatchLead"></p>
    <div id="mismatchTable"></div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Review-by-review detail</h2>
    <p class="lead">All <span id="totalN"></span> reviews scored — <span id="okN"></span> correct, <span id="badN"></span> mismatched.</p>
    <div class="filterbar">
      <div class="fgroup" data-role="verdict">
        <span class="flabel">Verdict</span>
        <div class="seg">
          <button data-v="All" class="active">All</button>
          <button data-v="Correct">Correct</button>
          <button data-v="Mismatched">Mismatched</button>
        </div>
      </div>
      <div class="fgroup" data-role="pred">
        <span class="flabel">Model said</span>
        <div class="seg">
          <button data-p="All" class="active">All</button>
          <button data-p="POSITIVE">POSITIVE</button>
          <button data-p="NEGATIVE">NEGATIVE</button>
        </div>
      </div>
      <div class="fgroup" data-role="derived">
        <span class="flabel">Rating-derived</span>
        <div class="seg">
          <button data-d="All" class="active">All</button>
          <button data-d="POSITIVE">POSITIVE</button>
          <button data-d="NEGATIVE">NEGATIVE</button>
        </div>
      </div>
      <div class="fgroup grow">
        <span class="flabel">Search title / text</span>
        <input id="kw" type="text" placeholder="Type a word…">
      </div>
      <div class="fcount">Showing <b id="shown">100</b> of 100 reviews</div>
      <button id="resetBtn" class="reset">Show all 100</button>
    </div>
    <div id="allTable"></div>
  </section>

  <p class="foot" id="foot"></p>
</div>

<script>
  const D = JSON.parse(document.getElementById('app-data').textContent);
  const rows = D.results, N = rows.length;
  const ok = rows.filter(r=>r.matched), bad = rows.filter(r=>!r.matched);
  const acc = ok.length/N;
  const cls = r=>r.correct_label;
  const pos = rows.filter(r=>cls(r)==='POSITIVE'), neg = rows.filter(r=>cls(r)==='NEGATIVE');
  const posOk = pos.filter(r=>r.matched).length, negOk = neg.filter(r=>r.matched).length;
  const predN = rows.filter(r=>r.model_prediction==='NEGATIVE').length;
  const predP = rows.filter(r=>r.model_prediction==='POSITIVE').length;
  const pct = f=> (f*100).toFixed(1);

  function kpi(label,value,detail){return `<div class="card kpi"><div class="label">${label}</div><div class="value">${value}</div><div class="detail">${detail}</div></div>`;}
  document.getElementById('kpis').innerHTML =
    kpi('Overall accuracy', pct(acc)+'%', `${ok.length}/${N} correct`) +
    kpi('Correct', ok.length, 'matched the rating-derived label') +
    kpi('Incorrect', bad.length, 'did not match the rating-derived label') +
    kpi('Reviews scored', N, 'first 100 in dataset order');

  const banner = document.getElementById('imbalanceBanner');
  banner.innerHTML = `<b>Read the accuracy with caution — this batch is lopsided.</b> ` +
    `${pos.length} of ${N} reviews (${pct(pos.length/N)}%) are rating-derived POSITIVE. ` +
    `A naive model that always answered POSITIVE would score ${pct(pos.length/N)}% with no skill at all. ` +
    `The real test is how it does on the rarer NEGATIVE class (${neg.length} reviews) and on the mismatches below.`;

  // Donut: correct-label split
  const posdeg = (pos.length/N)*360;
  const ring = document.createElement('div'); ring.className='ring';
  ring.style.setProperty('--posdeg', posdeg+'deg');
  ring.innerHTML = `<div class="inner"><b>${pct(pos.length/N)}%</b><span>POSITIVE</span><span class="sub2">${pct(neg.length/N)}% NEGATIVE</span></div>`;
  document.getElementById('donut').appendChild(ring);
  document.getElementById('imbalanceLegend').innerHTML =
    `<div class="lt">Reviews by class (rating-derived)</div>`+
    `<div><span class="dot" style="background:var(--pos)"></span>POSITIVE ${pos.length} (${pct(pos.length/N)}%)</div>`+
    `<div><span class="dot" style="background:var(--neg)"></span>NEGATIVE ${neg.length} (${pct(neg.length/N)}%)</div>`+
    `<div class="ms">Mismatches: ${bad.length} (not a class — shown separately)</div>`;

  function barRow(label, pctVal, text, color){
    return `<div class="bar-row"><span class="bl">${label}</span><span class="btrack"><span class="bfill" style="width:${pctVal}%;background:${color}"></span></span><span class="bval">${text}</span></div>`;
  }
  document.getElementById('correctBar').innerHTML =
    barRow('Correct', pct(ok.length/N), `${ok.length} (${pct(ok.length/N)}%)`, 'var(--pos)') +
    barRow('Mismatched', pct(bad.length/N), `${bad.length} (${pct(bad.length/N)}%)`, 'var(--neg)');

  document.getElementById('classAcc').innerHTML =
    barRow('POSITIVE', pos.length?pct(posOk/pos.length):0, `${posOk}/${pos.length}`, 'var(--pos)') +
    barRow('NEGATIVE', neg.length?pct(negOk/neg.length):0, `${negOk}/${neg.length}`, 'var(--neg)');

  // Mistakes cluster by class + direction
  const misLead = document.getElementById('mismatchLead');
  const badByClass = k=>bad.filter(r=>cls(r)===k).length;
  const dirN = bad.filter(r=>r.model_prediction==='NEGATIVE').length;
  const dirP = bad.filter(r=>r.model_prediction==='POSITIVE').length;
  misLead.innerHTML = `${bad.length} review${bad.length===1?'':'s'} did not match the rating-derived label. ` +
    `${badByClass('POSITIVE')} rating-derived POSITIVE review${badByClass('POSITIVE')===1?'':'s'} were predicted NEGATIVE, and ` +
    `${badByClass('NEGATIVE')} rating-derived NEGATIVE review${badByClass('NEGATIVE')===1?'':'s'} were predicted POSITIVE.`;

  function badge(pred){ return pred==='POSITIVE' ? '<span class="badge pos">POSITIVE</span>' : '<span class="badge neg">NEGATIVE</span>'; }
  function rowHtml(r, showMs=null){
    const ms = showMs
      ? `<tr><td><span class="badge ms">MISMATCH</span></td>
         <td>${r.rating}</td><td>${badge(r.correct_label)}</td><td>${badge(r.model_prediction)}</td>
         <td class="celltext"><span class="t">${r.title||'(no title)'}</span><span class="b">${r.text||'(no text)'}</span></td></tr>`
      : `<tr style="${r.matched?'':'background:var(--warn-bg)'}">
         <td>${r.rating}</td><td>${badge(r.correct_label)}</td><td>${badge(r.model_prediction)}</td>
         <td><span class="badge ${r.matched?'pos':'neg'}">${r.matched?'CORRECT':'MISMATCH'}</span></td>
         <td class="celltext"><span class="t">${r.title||'(no title)'}</span><span class="b">${r.text||'(no text)'}</span></td></tr>`;
  }
  const esc = s=>{const d=document.createElement('div');d.textContent=s;return d.innerHTML;};
  // note: titles/text inserted via DOM textContent-safe path below
  // (rowHtml uses template strings; we re-render with escaped values):
  const rowEsc = r=>`<tr ${r.matched?'':'style="background:var(--warn-bg)"'}>
     <td>${r.rating}</td>
     <td>${badge(r.correct_label)}</td><td>${badge(r.model_prediction)}</td>
     <td><span class="badge ${r.matched?'pos':'neg'}">${r.matched?'CORRECT':'MISMATCH'}</span></td>
     <td class="celltext"><span class="t">${esc(r.title||'(no title)')}</span><span class="b">${esc(r.text||'(no text)')}</span></td></tr>`;

  const mism = document.getElementById('mismatchTable');
  let mh = `<table><thead><tr><th>Status</th><th>Rating</th><th>Correct label</th><th>Model said</th><th>Review</th></tr></thead><tbody>`;
  mh += bad.map(r=>`<tr><td><span class="badge ms">MISMATCH</span></td><td>${r.rating}</td><td>${badge(r.correct_label)}</td><td>${badge(r.model_prediction)}</td><td class="celltext full"><span class="t">${esc(r.title||'(no title)')}</span><span class="b">${esc(r.text||'(no text)')}</span></td></tr>`).join('');
  mism.innerHTML = mh + `</tbody></table>`;

  document.getElementById('totalN').textContent = N;
  document.getElementById('okN').textContent = ok.length;
  document.getElementById('badN').textContent = bad.length;

  // ---- Step 4: interactive filtering ----
  function applyFilters(rws, f){
    const q = (f.q||'').trim().toLowerCase();
    return rws.filter(r=>{
      if(f.verdict==='Correct' && !r.matched) return false;
      if(f.verdict==='Mismatched' && r.matched) return false;
      if(f.pred!=='All' && r.model_prediction!==f.pred) return false;
      if(f.derived!=='All' && r.correct_label!==f.derived) return false;
      if(q){ const blob=(r.title||'')+' '+(r.text||''); if(blob.toLowerCase().indexOf(q)===-1) return false; }
      return true;
    });
  }
  function renderRows(rs){
    document.getElementById('allTable').innerHTML =
      `<table><thead><tr><th>Rating</th><th>Correct label</th><th>Model said</th><th>Verdict</th><th>Review</th></tr></thead><tbody>`+
      rs.map(rowEsc).join('')+`</tbody></table>`;
  }
  const state = {verdict:'All', pred:'All', derived:'All', q:''};
  function update(){
    const fr = applyFilters(rows, state);
    document.getElementById('shown').textContent = fr.length;
    renderRows(fr);
  }
  document.querySelectorAll('.filterbar .seg button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const group = btn.closest('.fgroup'); const role = group.dataset.role;
      if(role==='verdict') state.verdict = btn.dataset.v;
      if(role==='pred') state.pred = btn.dataset.p;
      if(role==='derived') state.derived = btn.dataset.d;
      group.querySelectorAll('button').forEach(b=>b.classList.toggle('active', b===btn));
      update();
    });
  });
  document.getElementById('kw').addEventListener('input', e=>{ state.q = e.target.value; update(); });
  document.getElementById('resetBtn').addEventListener('click', ()=>{
    state.verdict='All'; state.pred='All'; state.derived='All'; state.q='';
    document.getElementById('kw').value='';
    document.querySelectorAll('.filterbar .seg button').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.filterbar .seg').forEach(g=>g.querySelector('button').classList.add('active'));
    update();
  });
  update();

  const s = D.settings;
  document.getElementById('foot').textContent =
    `Source of truth: outputs/step2_results.json · ${N} reviews, first 100 in dataset order · ` +
    `Model ${s.model} · temperature ${s.temperature} · max_tokens ${s.max_tokens} · enable_thinking=false · ` +
    `Correct label rule: rating ≥ 4 → POSITIVE, else NEGATIVE · Model input was title + text only (rating never shown to the model).`;
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__DATA_JSON__", data_json)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("WROTE", OUT, f"({len(html):,} bytes)")
print("embedded reviews:", len(payload["results"]))
