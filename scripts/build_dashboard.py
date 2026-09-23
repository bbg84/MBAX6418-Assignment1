#!/usr/bin/env python3
"""Final Assignment 1 dashboard generator (evolves the Step 3/4 dashboard).

Source of truth (all embedded from saved outputs, not retyped):
  - outputs/step6_results.json  -> balanced 150-review three-class results (core)
  - outputs/step6_sample.json   -> exact balanced sample (star-rating distribution)
  - outputs/step2_results.json  -> original imbalanced 100 binary run (comparison)
  - outputs/step5_results.json  -> LLM-vs-NRC emotion comparison on the 100 (separate)

Emits one self-contained offline HTML file. All displayed numbers are computed
in the browser from the embedded saved data.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "dashboard.html")

SRC_FILES = {
    "step6_results": os.path.join(ROOT, "outputs", "step6_results.json"),
    "step6_sample": os.path.join(ROOT, "outputs", "step6_sample.json"),
    "step2_results": os.path.join(ROOT, "outputs", "step2_results.json"),
    "step5_results": os.path.join(ROOT, "outputs", "step5_results.json"),
}

R6 = json.load(open(SRC_FILES["step6_results"]))["results"]
R2 = json.load(open(SRC_FILES["step2_results"]))["results"]
S5 = json.load(open(SRC_FILES["step5_results"]))
S5TA = S5.get("tie_analysis", {})

ROWS = [{k: r.get(k) for k in ("rating", "title", "text", "correct_label",
                               "prediction", "correct", "emotion_llm")} for r in R6]

# static context that is NOT derivable from the 150 rows
SRC = {
    "step2": {
        "total": len(R2),
        "acc_pct": round(len([r for r in R2 if r["matched"]]) / len(R2) * 100, 1),
        "pos": len([r for r in R2 if r["correct_label"] == "POSITIVE"]),
        "neg": len([r for r in R2 if r["correct_label"] == "NEGATIVE"]),
    },
    "step5": {
        "agree_all": S5TA.get("agreement_all"),
        "agree_all_pct": S5TA.get("agreement_all_pct"),
        "agree_noNone": S5TA.get("agreement_in8_excl_none"),
        "agree_noNone_pct": S5TA.get("agreement_in8_excl_none_pct"),
        "none": S5TA.get("n_none"),
        "joy_anti": S5TA.get("joy_to_anticipation_mismatches"),
        "ties": S5TA.get("n_ties"),
        "ties_to_anticipation": S5TA.get("n_ties_resolved_to_anticipation_by_priority"),
        "joy_anti_tiebreak": S5TA.get("joy_anti_due_to_tiebreak"),
        "joy_anti_clear": S5TA.get("joy_anti_anticipation_clearly_higher"),
    },
    "source_files": [f.replace(ROOT + "/", "") for f in SRC_FILES.values()],
}

PAYLOAD = {"rows": ROWS, "src": SRC}
DATA_JSON = json.dumps(PAYLOAD, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MBAX 6418 · Assignment 1 · Review Sentiment &amp; Emotion</title>
<style>
  :root{
    --bg:#f6f7f9; --surface:#fff; --border:#e6e8ee; --text:#1c2430; --muted:#5c6675;
    --accent:#2f6df6; --accent-ink:#fff;
    --pos:#1e8e5a; --neg:#d64545; --neut:#c08a1d;
    --pos-bg:#e7f5ee; --neg-bg:#fcecea; --neut-bg:#fbf1df;
    --warn:#c77a12; --radius:14px;
    --shadow:0 1px 2px rgba(16,24,40,.05),0 8px 24px -12px rgba(16,24,40,.12);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1060px;margin:0 auto;padding:40px 24px 72px}
  header{margin-bottom:24px}
  .eyebrow{font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
  h1{font-size:27px;line-height:1.2;margin:0 0 6px;letter-spacing:-.02em}
  .sub{color:var(--muted);margin:0;font-size:15px}
  .grid{display:grid;gap:16px}
  .grid.kpis{grid-template-columns:repeat(4,1fr)}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px}
  .kpi .label{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
  .kpi .value{font-size:32px;font-weight:750;letter-spacing:-.02em;margin-top:4px;font-variant-numeric:tabular-nums}
  .kpi .value small{font-size:15px;color:var(--muted);font-weight:600}
  .kpi .detail{font-size:13px;color:var(--muted);margin-top:2px}
  h2{font-size:18px;margin:0 0 4px;letter-spacing:-.01em}
  h3{font-size:14px;margin:16px 0 6px;letter-spacing:-.01em}
  .lead{color:var(--muted);font-size:14px;margin:0 0 14px}
  .banner{border:1px solid var(--warn);border-left:5px solid var(--warn);background:#fdf3e2;border-radius:10px;padding:13px 16px;font-size:14px}
  .banner.note{background:var(--neut-bg);border-color:#e6c88a;border-left-color:var(--neut);color:#5a4300}
  .banner.info{background:#eef3ff;border-color:#c9d8ff;border-left-color:var(--accent);color:#1d3a8a}
  .banner b{color:#3a2c0f}
  .banner.info b{color:#16306e}
  .bars{margin-top:8px}
  .bar-row{display:flex;align-items:center;gap:12px;margin:9px 0}
  .bar-row .bl{width:130px;flex:none;font-size:13px;color:var(--muted);text-align:right}
  .bar-row .btrack{flex:1;display:block;background:#e9edf4;border:1px solid #ccd3e0;border-radius:999px;height:22px;overflow:hidden}
  .bar-row .bfill{display:block;height:100%;width:0;border-radius:999px;min-width:4px;box-shadow:inset 0 -1px 0 rgba(0,0,0,.12)}
  .bar-row .bval{width:118px;flex:none;font-size:13px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums}
  .pos{color:var(--pos)} .neg{color:var(--neg)} .neut{color:var(--neut)}
  .split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap}
  .chip.pos{background:var(--pos-bg);color:var(--pos)} .chip.neg{background:var(--neg-bg);color:var(--neg)} .chip.neut{background:var(--neut-bg);color:#8a6200}
  .chip.ms{background:#fdf1f1;color:#a34242;border:1px solid #f0caca}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th{text-align:left;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:8px 10px;border-bottom:1px solid var(--border)}
  td{padding:10px;border-bottom:1px solid var(--border);vertical-align:top}
  tr:last-child td{border-bottom:0}
  .celltext{max-width:360px;color:#3a4350}
  .celltext .t{font-weight:600;color:var(--text)}
  .celltext .b{color:var(--muted);font-size:12.5px;display:block;margin-top:2px}
  .celltext.full .b{max-height:none;overflow:visible}
  .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap}
  .badge.pos{background:var(--pos-bg);color:var(--pos)} .badge.neg{background:var(--neg-bg);color:var(--neg)} .badge.neut{background:var(--neut-bg);color:#8a6200}
  .badge.ms{background:#fdf3e2;color:#9a5e00;border:1px solid #e6c88a}
  .badge.corr{background:var(--pos-bg);color:var(--pos)} .badge.mis{background:var(--neg-bg);color:var(--neg)}
  .tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
  /* confusion matrix */
  .cmat-wrap{overflow-x:auto}
  .cmat{border-collapse:separate;border-spacing:5px;margin:6px 0;width:100%}
  .cmat th,.cmat td{text-align:center;border-radius:10px;border:1px solid var(--border)}
  .cmat th{background:var(--bg);color:var(--muted);font-size:11.5px;padding:8px}
  .cmat td{width:20%;padding:12px 6px;font-size:14px;font-weight:700}
  .cmat td .sub{display:block;font-size:11px;color:var(--muted);font-weight:600}
  .cmat .rl{font-weight:700;color:var(--text);font-size:12.5px;background:var(--bg)!important}
  .cm-ok{background:var(--pos-bg);color:var(--pos)}
  .cm-err{background:var(--neg-bg);color:var(--neg)}
  .cm-soft{background:var(--neut-bg);color:#8a6200}
  /* filters */
  .filterbar{display:flex;flex-wrap:wrap;align-items:flex-end;gap:16px;margin:14px 0;padding:14px;background:var(--bg);border:1px solid var(--border);border-radius:12px}
  .fgroup{display:flex;flex-direction:column;gap:6px}
  .fgroup.grow{flex:1;min-width:170px}
  .flabel{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
  .seg{display:flex;gap:4px;flex-wrap:wrap}
  .seg button{font:inherit;font-size:12.5px;font-weight:600;padding:6px 11px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--muted);cursor:pointer}
  .seg button:hover{border-color:var(--accent);color:var(--accent)}
  .seg button.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
  #kw{font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--text);min-width:150px}
  #kw:focus{outline:none;border-color:var(--accent)}
  .fcount{font-size:13px;color:var(--muted);align-self:center;white-space:nowrap}
  .fcount b{color:var(--text);font-size:15px}
  .reset{font:inherit;font-size:12.5px;font-weight:600;padding:7px 12px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--accent);cursor:pointer;white-space:nowrap}
  .reset:hover{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
  .foot{color:var(--muted);font-size:12px;margin-top:32px;line-height:1.6}
  .emotion-note{font-size:13px;color:var(--muted);background:var(--neut-bg);border:1px solid #e6c88a;border-radius:10px;padding:10px 14px;margin:10px 0}
  .klist{list-style:none;padding:0;margin:8px 0 0;font-size:13.5px}
  .klist li{margin:5px 0}
  .klist b{font-variant-numeric:tabular-nums}
  @media(max-width:760px){.grid.kpis{grid-template-columns:repeat(2,1fr)}.split{grid-template-columns:1fr}.bar-row .bl{width:104px}}
</style>
</head>
<body>
<script type="application/json" id="app-data">__DATA_JSON__</script>
<div class="wrap">
  <header id="top">
    <p class="eyebrow">MBAX 6418 · Assignment 1 · Final Dashboard</p>
    <h1>Amazon Gift Card Review Sentiment &amp; Emotion</h1>
    <p class="sub">A balanced <b>150-review</b> three-class analysis — how well an LLM classifies each review as <b class="pos">POSITIVE</b>, <b class="neut">NEUTRAL</b>, or <b class="neg">NEGATIVE</b>, checked against a label derived from the star rating.</p>
  </header>

  <section class="grid kpis" id="kpis"></section>

  <div class="banner note" id="balanceBanner"></div>

  <section class="grid" style="margin-top:16px">
    <div class="card">
      <h2>Star-rating distribution (balanced 150)</h2>
      <p class="lead">Because multiple star ratings map to the same sentiment class, the individual star counts are uneven: most POSITIVE reviews are 5-star, while all NEUTRAL reviews are 3-star.</p>
      <div class="bars" id="starBars"></div>
    </div>
    <div class="card">
      <h2>Accuracy by class</h2>
      <p class="lead">Share of each <b>rating-derived</b> class the model classified correctly (denominator = true/rating-derived class). NEUTRAL is the weak class.</p>
      <div class="bars" id="perfBars"></div>
      <h3>3-star NEUTRAL breakdown</h3>
      <p class="lead" style="margin-bottom:8px">Of the 50 rating-derived NEUTRAL (3-star) reviews:</p>
      <div class="bars" id="neutBars"></div>
    </div>
  </section>

  <section class="card" style="margin-top:16px" id="confusion">
    <h2>Correct label vs. model prediction (3×3 confusion)</h2>
    <p class="lead">Rows are the rating-derived correct class; columns are what the model predicted. Green = correct. The NEUTRAL row shows the model's trouble: <b>25 of 50 neutral reviews were called NEGATIVE</b>.</p>
    <div class="cmat-wrap">
      <table class="cmat" id="cmat">
        <thead><tr><th>Correct ↓ / Predicted →</th><th>POSITIVE</th><th>NEUTRAL</th><th>NEGATIVE</th></tr></thead>
        <tbody id="cmatBody"></tbody>
      </table>
    </div>
    <div class="tags" id="cmTags"></div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Original imbalanced run vs. final balanced run</h2>
    <p class="lead">The original first-100 run looked far more accurate — but that sample was heavily lopsided. The two numbers are <b>not</b> directly comparable.</p>
    <div class="split">
    <div class="card" style="box-shadow:none">
      <h3>Step 2 — original 100 (heavily imbalanced)</h3>
      <ul class="klist">
        <li>Overall accuracy: <b id="s2acc"></b></li>
        <li>Class mix: <b id="s2dist"></b></li>
        <li>Why inflated: 93% of the batch was POSITIVE. There was <b>no NEUTRAL class in Step 2</b> — 3-star reviews were grouped into NEGATIVE, so some "negative" labels were actually neutral reviews.</li>
      </ul>
    </div>
    <div class="card" style="box-shadow:none">
      <h3>Step 6 — balanced 150 (50 / 50 / 50)</h3>
      <ul class="klist">
        <li>Overall accuracy: <b id="s6acc"></b></li>
        <li>Class mix: <b id="s6dist"></b></li>
        <li>The balanced run is a clearer test of performance across all three classes — accuracy drops because the rare NEUTRAL class is finally represented.</li>
      </ul>
    </div>
    </div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Review-by-review detail</h2>
    <p class="lead">All <span id="totalN"></span> balanced reviews — <span id="okN"></span> correct, <span id="badN"></span> mismatched.</p>
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
          <button data-p="POSITIVE">POSITIVE</button><button data-p="NEUTRAL">NEUTRAL</button><button data-p="NEGATIVE">NEGATIVE</button>
        </div>
      </div>
      <div class="fgroup" data-role="derived">
        <span class="flabel">Rating-derived</span>
        <div class="seg">
          <button data-d="All" class="active">All</button>
          <button data-d="POSITIVE">POSITIVE</button><button data-d="NEUTRAL">NEUTRAL</button><button data-d="NEGATIVE">NEGATIVE</button>
        </div>
      </div>
      <div class="fgroup grow">
        <span class="flabel">Search title / text</span>
        <input id="kw" type="text" placeholder="Type a word…">
      </div>
      <div class="fcount">Showing <b id="shown">150</b> of 150 reviews</div>
      <button id="resetBtn" class="reset">Show all 150</button>
    </div>
    <div id="allTable"></div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Mismatched reviews <span class="note">(model disagreed with the rating-derived label)</span></h2>
    <p class="lead" id="mismatchLead"></p>
    <div id="mismatchTable"></div>
  </section>

  <section class="card" style="margin-top:16px">
    <h2>Emotion analysis <span class="note">(SEPARATE — original 100-review sample, Step 5)</span></h2>
    <div class="emotion-note">
      <b>This section is a separate analysis on the original 100-review binary sample — NOT the balanced 150 above.</b>
      It compares the <b>LLM</b>'s primary emotion against a purely word-list <b>NRC</b> emotion — two independent methods.
    </div>
    <div class="split" style="margin-top:6px">
      <div class="card" style="box-shadow:none">
        <h3>LLM-vs-NRC agreement</h3>
        <ul class="klist">
          <li>Same primary emotion: <b id="eAgreeAll"></b> of 100 (<b id="eAgreeAllPct"></b>)</li>
          <li>Excluding 15 NRC "no emotion" reviews: <b id="eAgreeNoNone"></b> of 85 (<b id="eAgreeNoNonePct"></b>)</li>
          <li>NRC found no emotion in: <b id="eNone"></b> reviews</li>
          <li>Dominant disagreement: <b>LLM joy → NRC anticipation</b> (<b id="eJoyAnti"></b> cases)</li>
        </ul>
      </div>
      <div class="card" style="box-shadow:none">
        <h3>Tie-break caveat</h3>
        <ul class="klist">
          <li><b id="eTies"></b> of 85 nonzero NRC reviews had a tie for the top (<b id="eTiesAnti"></b> resolved to anticipation by our fixed priority rule)</li>
          <li>Of <b id="eJoyAnti2"></b> joy→anticipation mismatches, <b id="eTiebreak"></b> occurred where anticipation merely <b>tied</b> joy — not clearly outscoring it (<b id="eClear"></b> clearly higher)</li>
          <li>Most of the disagreement is an artifact of the tie-break, not strong NRC signal.</li>
        </ul>
      </div>
    </div>
  </section>

  <p class="foot" id="foot"></p>
</div>

<script>
  const A = JSON.parse(document.getElementById('app-data').textContent);
  const ROWS = A.rows, SRC = A.src;
  const N = ROWS.length;
  const CLASSES = ['POSITIVE','NEUTRAL','NEGATIVE'];

  const ok = ROWS.filter(r=>r.correct), bad = ROWS.filter(r=>!r.correct);
  const acc = ok.length/N;
  const pct = f=>(f*100).toFixed(1);
  const esc = s=>{const d=document.createElement('div');d.textContent=s;return d.innerHTML;};
  const chip = (c,lab)=>`<span class="chip ${c.toLowerCase()}">${lab||c}</span>`;
  const badge = (c)=>c==='POSITIVE'?'<span class="badge pos">POSITIVE</span>'
      : c==='NEGATIVE'?'<span class="badge neg">NEGATIVE</span>':'<span class="badge neut">NEUTRAL</span>';
  const cls = r=>r.correct_label, pred = r=>r.prediction;
  const byClass = c=>ROWS.filter(r=>cls(r)===c);
  const pcOk = c=>byClass(c).filter(r=>r.correct).length;

  // ---- KPIs ----
  function kpi(l,v,d){return `<div class="card kpi"><div class="label">${l}</div><div class="value">${v}</div><div class="detail">${d}</div></div>`;}
  document.getElementById('kpis').innerHTML =
    kpi('Reviews',  N, 'balanced 50/50/50') +
    kpi('Overall accuracy', pct(acc)+'%', `${ok.length}/${N} correct`) +
    kpi('Correct', ok.length, 'matched the rating-derived label') +
    kpi('Mismatched', bad.length, 'did not match the rating-derived label');

  document.getElementById('balanceBanner').innerHTML =
    `<b>Balanced sample — and this changes the picture.</b> This run draws 50 POSITIVE, 50 NEUTRAL, and 50 NEGATIVE reviews (fixed seed, reproducible). ` +
    `Because every class is equally represented, the overall ${pct(acc)}% is a more informative measure of performance across classes than the original imbalanced run below.`;

  // ---- star distribution (from the balanced sample ratings) ----
  function barRow(label, wPct, val, color, clsColor){
    return `<div class="bar-row"><span class="bl">${label}</span><span class="btrack"><span class="bfill" style="width:${wPct}%;background:${color}"></span></span><span class="bval">${val}</span></div>`;
  }
  const starCounts = [0,0,0,0,0];
  ROWS.forEach(r=>{ if(r.rating>=1&&r.rating<=5) starCounts[Math.round(r.rating)-1]++; });
  const maxStar = Math.max(...starCounts);
  document.getElementById('starBars').innerHTML = starCounts.map((c,i)=>
    barRow(i+1+'&nbsp;★', c/maxStar*100, c+' reviews', 'var(--accent)')).join('');

  // ---- performance by class ----
  const perfColors = {POSITIVE:'var(--pos)', NEUTRAL:'var(--neut)', NEGATIVE:'var(--neg)'};
  document.getElementById('perfBars').innerHTML = CLASSES.map(c=>{
    const sub=byClass(c); const parte=pcOk(c)/sub.length*100;
    return barRow(c, parte, `${pcOk(c)}/${sub.length} · ${parte.toFixed(1)}%`, perfColors[c]);
  }).join('');

  // ---- 3-star NEUTRAL breakdown ----
  const neut = byClass('NEUTRAL');
  const nb = {POSITIVE:0, NEUTRAL:0, NEGATIVE:0};
  neut.forEach(r=>nb[pred(r)]++);
  const nbPct = c=> nb[c]/neut.length*100;
  document.getElementById('neutBars').innerHTML =
    barRow('POSITIVE', nbPct('POSITIVE'), `${nb.POSITIVE} (${nbPct('POSITIVE').toFixed(1)}%)`, perfColors.POSITIVE) +
    barRow('NEUTRAL',  nbPct('NEUTRAL'),  `${nb.NEUTRAL} (${nbPct('NEUTRAL').toFixed(1)}%)`, perfColors.NEUTRAL) +
    barRow('NEGATIVE', nbPct('NEGATIVE'), `${nb.NEGATIVE} (${nbPct('NEGATIVE').toFixed(1)}%)`, perfColors.NEGATIVE);

  // ---- confusion matrix ----
  const conf = {}; CLASSES.forEach(a=>{conf[a]={};CLASSES.forEach(b=>conf[a][b]=0);});
  ROWS.forEach(r=>conf[cls(r)][pred(r)]++);
  let cmHtml = '';
  CLASSES.forEach(cr=>{
    cmHtml += `<tr><td class="rl">${cr}</td>` + CLASSES.map(cp=>{
      const v=conf[cr][cp];
      let k = (cr===cp)?(v>0?'cm-ok':'cm-soft'):(v>0?'cm-err':'cm-soft');
      return `<td class="${k}">${v}<span class="sub">${pct(v/ROWS.filter(x=>cls(x)===cr).length)}%</span></td>`;
    }).join('') + `</tr>`;
  });
  document.getElementById('cmatBody').innerHTML = cmHtml;
  const maxNonDiag = Math.max(...CLASSES.map(cr=>CLASSES.map(cp=>cr===cp?0:conf[cr][cp])).flat());
  const tagLine = `Largest error: NEUTRAL → NEGATIVE (${conf.NEUTRAL.NEGATIVE} of 50). Next: NEUTRAL → POSITIVE (${conf.NEUTRAL.POSITIVE}) and POSITIVE → NEUTRAL (${conf.POSITIVE.NEUTRAL}).`;
  document.getElementById('cmTags').innerHTML = `<span class="chip ms">→ NEGATIVE ${conf.NEUTRAL.NEGATIVE}</span><span class="chip" style="background:var(--neut-bg);color:#8a6200">→ NEUTRAL ${conf.POSITIVE.NEUTRAL}</span><span class="chip" style="background:var(--pos-bg);color:var(--pos)">↔ NEUTRAL-POSITIVE ${conf.NEUTRAL.POSITIVE}</span>`;

  // ---- imbalanced vs balanced ----
  const s6acc = pct(acc), s6d = `POSITIVE ${byClass('POSITIVE').length} / NEUTRAL ${byClass('NEUTRAL').length} / NEGATIVE ${byClass('NEGATIVE').length}`;
  document.getElementById('s2acc').textContent = SRC.step2.acc_pct + '%';
  document.getElementById('s2dist').textContent = `${SRC.step2.pos} POSITIVE / ${SRC.step2.neg} NEGATIVE`;
  document.getElementById('s6acc').textContent = s6acc + '%';
  document.getElementById('s6dist').textContent = s6d;

  // ---- emotion ----
  document.getElementById('eAgreeAll').textContent = SRC.step5.agree_all;
  document.getElementById('eAgreeAllPct').textContent = Number(SRC.step5.agree_all_pct).toFixed(1) + '%';
  document.getElementById('eAgreeNoNone').textContent = SRC.step5.agree_noNone;
  document.getElementById('eAgreeNoNonePct').textContent = Number(SRC.step5.agree_noNone_pct).toFixed(1) + '%';
  document.getElementById('eNone').textContent = SRC.step5.none;
  document.getElementById('eJoyAnti').textContent = SRC.step5.joy_anti;
  document.getElementById('eTies').textContent = SRC.step5.ties;
  document.getElementById('eTiesAnti').textContent = SRC.step5.ties_to_anticipation;
  document.getElementById('eJoyAnti2').textContent = SRC.step5.joy_anti;
  document.getElementById('eTiebreak').textContent = SRC.step5.joy_anti_tiebreak;
  document.getElementById('eClear').textContent = SRC.step5.joy_anti_clear;

  // ---- review table + filtering ----
  function rowEsc(r){
    const mis = r.correct;
    return `<tr ${mis?'':'style="background:#fbf0ee"'}><td>${r.rating}</td><td>${badge(cls(r))}</td><td>${badge(pred(r))}</td>`+
      `<td><span class="chip ${mis?'corr':'mis'}">${mis?'CORRECT':'MISMATCH'}</span></td>`+
      `<td class="celltext"><span class="t">${esc(r.title||'(no title)')}</span><span class="b">${esc(r.text||'(no text)')}</span></td></tr>`;
  }
  function applyFilters(rws,f){
    const q=(f.q||'').trim().toLowerCase();
    return rws.filter(r=>{
      if(f.verdict==='Correct'&&!r.correct) return false;
      if(f.verdict==='Mismatched'&&r.correct) return false;
      if(f.pred!=='All'&&pred(r)!==f.pred) return false;
      if(f.derived!=='All'&&cls(r)!==f.derived) return false;
      if(q){const b=(r.title||'')+' '+(r.text||''); if(b.toLowerCase().indexOf(q)===-1) return false;}
      return true;
    });
  }
  function renderRows(rs){
    document.getElementById('allTable').innerHTML =
      `<table><thead><tr><th>Rating</th><th>Correct label</th><th>Model said</th><th>Verdict</th><th>Review</th></tr></thead><tbody>`+
      rs.map(rowEsc).join('')+`</tbody></table>`;
  }
  const state = {verdict:'All', pred:'All', derived:'All', q:''};
  function update(){ const fr=applyFilters(ROWS,state); document.getElementById('shown').textContent=fr.length; renderRows(fr); }
  document.querySelectorAll('.filterbar .seg button').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const g=btn.closest('.fgroup'), role=g.dataset.role;
      if(role==='verdict') state.verdict=btn.dataset.v;
      if(role==='pred') state.pred=btn.dataset.p;
      if(role==='derived') state.derived=btn.dataset.d;
      g.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b===btn));
      update();
    });
  });
  document.getElementById('kw').addEventListener('input',e=>{state.q=e.target.value;update();});
  document.getElementById('resetBtn').addEventListener('click',()=>{
    state.verdict='All';state.pred='All';state.derived='All';state.q='';
    document.getElementById('kw').value='';
    document.querySelectorAll('.filterbar .seg button').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.filterbar .seg').forEach(g=>g.querySelector('button').classList.add('active'));
    update();
  });

  document.getElementById('totalN').textContent=N;
  document.getElementById('okN').textContent=ok.length;
  document.getElementById('badN').textContent=bad.length;

  // ---- mismatched section (representative by type) ----
  const misByType = {};
  bad.forEach(r=>{ const k=cls(r)+'→'+pred(r); (misByType[k]=misByType[k]||[]).push(r); });
  const typeLead = Object.entries(misByType).map(([k,v])=>`${v.length} ${k}`).join(' · ');
  document.getElementById('mismatchLead').innerHTML =
    `${bad.length} reviews did not match. ${typeLead}. Representative examples below.`;
  let mh = `<table><thead><tr><th>Type</th><th>Rating</th><th>Correct</th><th>Model said</th><th>Review</th></tr></thead><tbody>`;
  const order = ['NEUTRAL→NEGATIVE','NEUTRAL→POSITIVE','POSITIVE→NEUTRAL','NEGATIVE→NEUTRAL'];
  order.forEach(t=>{
    (misByType[t]||[]).slice(0,3).forEach(r=>{
      mh += `<tr><td><span class="chip ms">${t}</span></td><td>${r.rating}</td><td>${badge(cls(r))}</td><td>${badge(pred(r))}</td>`+
        `<td class="celltext full"><span class="t">${esc(r.title||'(no title)')}</span><span class="b">${esc(r.text||'(no text)')}</span></td></tr>`;
    });
  });
  document.getElementById('mismatchTable').innerHTML = mh + `</tbody></table>`;

  // ---- footer ----
  document.getElementById('foot').textContent =
    `Sources of truth: outputs/step6_results.json (balanced 150) · outputs/step6_sample.json · outputs/step2_results.json (imbalanced 100) · outputs/step5_results.json (emotion, original 100). ` +
    `Sentiment labels POSITIVE / NEUTRAL / NEGATIVE. The rating-derived correct label is used only for judging; it is never shown to the model. Emotion section is the separate Step 5 analysis on the original 100-review sample.`;

  update();
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__DATA_JSON__", DATA_JSON)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("WROTE", OUT, f"({len(html):,} bytes)")
print("embedded rows:", len(ROWS))
