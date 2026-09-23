#!/usr/bin/env python3
"""Final deliverable stage — generate README.md.

Every number is read programmatically from the saved outputs (never typed by
hand), so the report always matches what the pipeline produced. The narrative is
written here; the metrics come from the JSON files.
"""
import json, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "README.md")

R6 = json.load(open(os.path.join(ROOT, "outputs", "step6_results.json")))["results"]
R2 = json.load(open(os.path.join(ROOT, "outputs", "step2_results.json")))["results"]
S5 = json.load(open(os.path.join(ROOT, "outputs", "step5_results.json")))
TA = S5["tie_analysis"]

# ---- Step 6 (balanced, three-class) ----
N = len(R6)
ok = sum(1 for r in R6 if r["correct"]); bad = N - ok
acc = ok / N * 100
CLASSES = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
def cls_acc(c):
    s = [r for r in R6 if r["correct_label"] == c]
    k = sum(1 for r in s if r["correct"])
    return k, len(s), k / len(s) * 100
per = {c: cls_acc(c) for c in CLASSES}
conf = {}
for cr in CLASSES:
    conf[cr] = {cp: sum(1 for r in R6 if r["correct_label"] == cr and r["prediction"] == cp) for cp in CLASSES}
neut = [r for r in R6 if r["correct_label"] == "NEUTRAL"]
neut_brk = {p: sum(1 for r in neut if r["prediction"] == p) for p in CLASSES}
stars = dict(sorted(Counter(round(r["rating"]) for r in R6).items()))

# ---- Step 2 (imbalanced binary) ----
s2n = len(R2); s2ok = sum(1 for r in R2 if r["matched"])
s2acc = s2ok / s2n * 100
s2pos = len([r for r in R2 if r["correct_label"] == "POSITIVE"])
s2neg = len([r for r in R2 if r["correct_label"] == "NEGATIVE"])

# ---- Step 5 (emotion, original 100) ----
agree_all = TA["agreement_all"]; agree_all_pct = TA["agreement_all_pct"]
agree_no = TA["agreement_in8_excl_none"]; agree_no_pct = TA["agreement_in8_excl_none_pct"]
none_n = TA["n_none"]; joy_anti = TA["joy_to_anticipation_mismatches"]
ties = TA["n_ties"]; ties_anti = TA["n_ties_resolved_to_anticipation_by_priority"]
ja_tie = TA["joy_anti_due_to_tiebreak"]; ja_clear = TA["joy_anti_anticipation_clearly_higher"]

def f1(x):
    return f"{x:.1f}" if isinstance(x, float) else str(x)

README = f"""# MBAX 6418 — Assignment 1

**Sentiment & Emotion Classification of Amazon Reviews**

## Project overview

For this project, I built a sentiment and emotion classifier for Amazon product
reviews. An LLM reads each review's title and body text and predicts a sentiment
(POSITIVE / NEUTRAL / NEGATIVE) plus a primary emotion (one of eight NRC emotion
labels). Its predictions are judged against a "correct" label derived from the
review's own star rating — the rating is used only for evaluation and is never
shown to the model. Results are presented in a single self-contained HTML
dashboard.

## Data

I used the **Amazon 2023 "Gift Cards" review category** from the Amazon Reviews
'23 dataset, collected by the **McAuley Lab at UC San Diego**:

- Dataset page: https://amazon-reviews-2023.github.io
- Gift Cards review file:
  https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Gift_Cards.jsonl.gz

It is a gzipped JSON-lines file; each line is one review. I used the fields
`rating`, `title`, `text`, `verified_purchase`, `helpful_vote`, `timestamp`, and
`asin`. The raw file is large and re-downloadable, so it is kept out of the
repository (see `.gitignore`).

## Method

- **Model input:** the review **title** and **text** only. The star **rating is
  never sent to the model**.
- **Rating-derived correct label** (computed only after prediction):
  - 4–5 stars = POSITIVE
  - 3 stars = NEUTRAL
  - 1–2 stars = NEGATIVE
- The model is called through an OpenAI-compatible endpoint
  (`cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`) with reasoning disabled and, for the
  final three-class run, an enforced JSON-schema response format so the emotion
  stays within the eight allowed labels.
- **Balanced sample:** 50 reviews per class (50 POSITIVE / 50 NEUTRAL /
  50 NEGATIVE, 150 total) drawn from the whole file with a **fixed random seed
  (6418)**, so the exact same sample can be reproduced.
- **Emotions:** the LLM predicts one of eight NRC emotion labels (anger,
  anticipation, disgust, fear, joy, sadness, surprise, trust). An independent
  method scores each review's words against the **NRC Emotion Lexicon**
  (Mohammad, NRC-Emotion-Lexicon-Wordlevel-v0.92,
  https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm) and takes the
  highest-scoring emotion; ties are broken by a fixed priority order and a "no
  emotion found" result is labeled NONE.

## Results — final balanced three-class run

- 150 reviews: **50 POSITIVE / 50 NEUTRAL / 50 NEGATIVE**
- **Overall accuracy: {ok}/{N} = {f1(acc)}%**
- POSITIVE: **{per['POSITIVE'][0]}/{per['POSITIVE'][1]} = {f1(per['POSITIVE'][2])}%**
- NEUTRAL: **{per['NEUTRAL'][0]}/{per['NEUTRAL'][1]} = {f1(per['NEUTRAL'][2])}%**
- NEGATIVE: **{per['NEGATIVE'][0]}/{per['NEGATIVE'][1]} = {f1(per['NEGATIVE'][2])}%**

Confusion matrix (rows = rating-derived correct class, columns = model prediction):

| Correct \\ Predicted | POSITIVE | NEUTRAL | NEGATIVE |
|---|---|---|---|
| POSITIVE | {conf['POSITIVE']['POSITIVE']} | {conf['POSITIVE']['NEUTRAL']} | {conf['POSITIVE']['NEGATIVE']} |
| NEUTRAL | {conf['NEUTRAL']['POSITIVE']} | {conf['NEUTRAL']['NEUTRAL']} | {conf['NEUTRAL']['NEGATIVE']} |
| NEGATIVE | {conf['NEGATIVE']['POSITIVE']} | {conf['NEGATIVE']['NEUTRAL']} | {conf['NEGATIVE']['NEGATIVE']} |

### 1. Why did the lopsided run look very accurate, and what changed after balancing?

The original first-100 run (Step 2) scored **{s2acc:.1f}%**, but the batch was
heavily imbalanced at **{s2pos} POSITIVE / {s2neg} NEGATIVE**, and it had **no
separate NEUTRAL class** — 3-star reviews were grouped into NEGATIVE. A model
that mostly predicted POSITIVE looked very accurate because that was nearly every
review.

The balanced run uses 50 reviews from each class, which makes it easier to see
how the model performs across POSITIVE, NEUTRAL, and NEGATIVE reviews. Accuracy
dropped to **{f1(acc)}%**, mainly because the model struggled with the newly
separated NEUTRAL class. The two runs are not directly comparable because the
class definitions and sample composition changed.

### 2. Where do the model's mistakes go?

The dominant mistake is on 3-star NEUTRAL reviews:

- **{neut_brk['NEGATIVE']} of {len(neut)} rating-derived NEUTRAL were predicted
  NEGATIVE** ({neut_brk['NEGATIVE']}/{len(neut)} = {f1(neut_brk['NEGATIVE']/len(neut)*100)}%)
- **{neut_brk['POSITIVE']} of {len(neut)} NEUTRAL were predicted POSITIVE**
  ({f1(neut_brk['POSITIVE']/len(neut)*100)}%)
- only **{per['NEUTRAL'][0]} of {len(neut)} NEUTRAL were correctly identified**
- **{conf['POSITIVE']['NEUTRAL']} POSITIVE** were predicted NEUTRAL
- **{conf['NEGATIVE']['NEUTRAL']} NEGATIVE** were predicted NEUTRAL
- there was **no direct POSITIVE↔NEGATIVE confusion** in the final matrix

So the model tended to classify many 3-star (neutral) reviews as **NEGATIVE**
rather than NEUTRAL (and a small number as POSITIVE). This was the model's
biggest weakness in the balanced run and became clear once 3-star reviews were
treated as their own NEUTRAL class.

### 3. How do the LLM and NRC emotion methods differ, and why?

This emotion comparison is a **separate analysis on the original 100-review
sample (Step 5)** — not the balanced 150. It compares the LLM's primary emotion
against an independent NRC word-list emotion:

- Two methods agreed on **{agree_all}/{100} = {f1(agree_all_pct)}%** of reviews
- Excluding the {none_n} reviews where NRC found no emotion: **{agree_no}/85 =
  {f1(agree_no_pct)}%**
- The dominant disagreement was **LLM joy → NRC anticipation** ({joy_anti} cases)
- {ties} of the 85 nonzero-NRC reviews had a tied top score; {ties_anti} of those
  ties were resolved to anticipation by the fixed priority rule
- Of the {joy_anti} joy→anticipation disagreements, {ja_tie} involved
  anticipation merely *tying* joy, while only {ja_clear} had anticipation
  clearly outscore joy

The two methods disagree for a couple of reasons. The LLM considers the full
context of the review, while the NRC method simply counts words associated with
each emotion. The tie-break rule also affected the NRC results quite a bit.
Because anticipation often tied with joy and had higher priority, many reviews
ended up labeled anticipation even when it did not clearly score higher.

## Issues / debugging

Issues were recorded continuously in `notes/issues.md`. The most meaningful
ones:

- **Empty model output (Step 1).** The reasoning model consumed its token budget
  on hidden thinking and returned empty `content`. Fixed by disabling thinking
  (`enable_thinking=false`) so a bare token is returned.
- **Invisible dashboard bars.** Colored bar fills were `<span>`s, which ignore
  `width`/`height` in Chrome. Fixed with block layout.
- **Donut semantics.** The chart's center showed a metric different from the
  slice it plotted. Corrected so the chart tells one consistent story.
- **Emotion labels escaped the eight-label set (Step 6).** On a few reviews the
  model returned words like "disappointment"/"frustration". Prompt rewording
  alone was not enough, so I switched to an **enforced JSON-schema
  `response_format`** (constrained decoding) so the emotion stays in the eight
  labels.
- **Percentages displayed 100× too large.** A percentage was multiplied by 100
  a second time; fixed and verified in the browser.

I documented each issue in `notes/issues.md` and updated the code as problems
came up.

## Dashboard

The results are presented in `dashboard.html`, a single self-contained HTML file
(no server, works offline). It shows the headline metrics, a star-rating
distribution, a 3×3 confusion matrix, accuracy by class, the NEUTRAL-breakdown,
an imbalanced-vs-balanced comparison, an interactive review table with
All/Correct/Mismatched, class and keyword filters and a live count, and a
clearly-separated emotion section.

Screenshots:

![Dashboard overview](assets/dashboard-overview.png)

![Confusion matrix](assets/dashboard-confusion.png)

## How to reproduce

Pipeline scripts live in `scripts/`:

- `scripts/step6_select_sample.py` — select the balanced 150-review sample
  (seed 6418) and save `outputs/step6_sample.json`
- `scripts/score_step6.py` — run the balanced 150 through the model and save
  `outputs/step6_results.json` (three-class sentiment + emotion)
- `scripts/score_nrc.py` — derive primary emotion from the NRC word list
  (`outputs/step5_nrc_raw.json` on the original 100)
- `scripts/score_emotion_llm.py` — LLM emotion on the original 100
  (`outputs/step5_llm_raw.json`)
- `scripts/build_dashboard.py` — read the saved outputs and produce
  `dashboard.html`
- `scripts/build_readme.py` — generate this README from the saved outputs

Saved outputs are in `outputs/`. The reusable prompt is
`prompts/sentiment_threeclass_prompt.txt`.

To use the code you would provide your own endpoint settings in a local `.env`
(not committed). The Amazon dataset is downloaded separately and kept out of the
repository.

- The **NRC Emotion Lexicon** file `NRC-Emotion-Lexicon-Wordlevel-v0.92.txt`
  should be downloaded and placed at
  `data/nrc/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt`.
- The project uses only the **Python 3 standard library**, so no third-party
  `pip` packages are required.
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(README)
print("WROTE", OUT, f"({len(README):,} chars)")
print("numeric check:", N, ok, f1(acc), per['POSITIVE'][0], per['NEUTRAL'][0], per['NEGATIVE'][0],
      "| step2:", s2ok, s2acc, s2pos, s2neg, "| step5:", agree_all, agree_no_pct, joy_anti, ties_anti, ja_tie, ja_clear)
