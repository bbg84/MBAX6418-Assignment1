# Issues Log (for the final report's "bugs/issues encountered" section)

Each entry: what happened, the cause, and how we worked around it.

## 1. Reasoning-model empty response → empty `content` (Step 1 spot-check)

- **When:** First Step 1 spot-check call to the course classification endpoint.
- **Symptom:** Model returned `content: null` and `finish_reason: length`; the
  classification came back empty, so the caller crashed and produced no answer.
- **Cause:** The served model (`cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`) is a
  *reasoning* model. In its default mode it emits a hidden "thinking" chain
  before the final answer. Our call set `max_tokens=10`, so all 10 tokens were
  consumed by the reasoning phase and the model ran out of budget before
  producing the visible answer (`completion_tokens_details.reasoning_tokens`
  = 10, `finish_reason: length`).
- **Fix:** Two working options confirmed —
    1. Give the model a large token budget (e.g. `max_tokens=300`) and let it
       finish reasoning; the answer then appears in `content` (with leading
       whitespace to strip).
    2. **Chosen:** Disable thinking entirely with
       `chat_template_kwargs: {"enable_thinking": false}`. This makes the model
       skip reasoning and return exactly the bare token in `content`
       (e.g. `"NEGATIVE"`), ~3 completion tokens, `finish_reason: stop`.
       This also keeps responses small, fast, and exactly one token.
- **Prompt impact:** None — the prompt file is unchanged. The fix is in the
  endpoint-call parameters.
- **Lesson for the project:** always disable thinking for this endpoint when we
  want a bare classification token.

## 2. Invisible bar fills (Step 3, found during user Chrome review)

- **When:** Step 3 dashboard, first browser review.
- **Symptom:** "Correct vs. incorrect" and "Performance by class" bars appeared
  as empty light-gray tracks; the colored fills were invisible.
- **Cause:** The fill was a `<span>`. Inline-level elements ignore `width` and
  `height` in Chrome, so the `width:X%` never applied and the fill never grew.
- **Fix:** Set `display:block` on both the track and the fill so the CSS width
  is honored; made tracks bordered/contrasting and fills `min-width:4px` so the
  small 3% bar can't vanish.

## 3. Donut center contradicted the chart (Step 3)

- **When:** Step 3 review.
- **Symptom:** The donut showed the 93/7 POSITIVE/NEGATIVE class split, but its
  center read "97.0% accurate" — a different metric, so the chart misled.
- **Fix:** Center now summarizes the class split shown: "93.0% POSITIVE /
  7.0% NEGATIVE". Accuracy remains in the KPI cards where it belongs. "Mismatch"
  was also removed from the class legend (it is not a distribution slice) and
  shown separately.

## 4. Couldn't verify live clicks in the Hermes preview pane (Step 4)

- **When:** Step 4 filtering verification.
- **Symptom:** Clicking a filter in the preview-pane file tab did not show up in
  the pane's captured text — the snapshot stayed at the initial 100-row render.
- **Cause:** The preview pane's file-tab text reader returns a render-time
  snapshot and wasn't reflecting later DOM state changes from programmatic
  clicks; this is a tooling limitation, not a dashboard bug.
- **Fix / verification:** Exported the dashboard's actual `applyFilters` +
  click-wiring into a DOM-simulation harness in Node and drove the real click
  handlers there. Verified: All=100, Correct=97, Mismatched=3, rating-derived
  NEGATIVE=7, combined Mismatched+rating-derived POSITIVE=2, keyword "awesome"=3,
  reset=100 (with the search box cleared). The user confirmed the filters
  interactively in Chrome.

## 5. Step 5 coding bug fixed before running (undefined variable)

- **When:** writing `scripts/score_nrc.py`.
- **Symptom:** `primary()` returned `"NONE"` (a string) in one branch and a
  `(chosen, counts)` tuple in the other; the caller then did `res[0]`, which on
  `"NONE"` would have returned `"N"`. A leftover `detail` variable in a print
  was also undefined (caught by the linter before running).
- **Fix:** `primary()` now always returns a single emotion string; the caller
  uses the `counts` dict directly. Confirmed correct on a clean run.

## 6. Very low LLM-vs-NRC emotion agreement (22%) + LLM sentiment drift (Step 5)

- **Symptom (expected behavior, now measured):** only 22/100 reviews had the
  same primary emotion from both methods.
- **Cause (LLM side):** the LLM collapsed to `joy` on 88 of 100 reviews — it
  treated almost every positive review as joyful, so it rarely exercised the
  other 7 emotions.
- **Cause (NRC side):** with the fixed tie priority `anger → … → joy → sadness
  → surprise → trust`, many positive reviews tied `anticipation` with `joy`
  (e.g. words like "great", "easy", "gift") and the priority rule handed the
  win to `anticipation` (59 of 100). The most common single disagreement was
  `LLM joy -> NRC anticipation` (51 reviews).
- **Sentiment drift:** the extended prompt flipped 1 of 100 sentiment
  predictions versus Step 2 — row_index 46, "Love it!!" / "This is an online
  gift card nothing to show sorry", Step 2 NEGATIVE → Step 5 POSITIVE. This is
  the same ambiguous review flagged in the Step 1 spot-check; the new prompt
  changed how it was judged. Flagged, not hidden; nothing overwrote Step 2 data.

## 7. Emotion format violations on the three-class run (Step 6) — RESOLVED via constrained decoding

- **Symptom:** on the 150-review balanced run, the LLM sometimes returned an
  emotion outside the approved 8 — specifically `disappointment` and
  `frustration` (near-synonyms of sadness/anger).
- **What did NOT fully work:** strengthening
  `prompts/sentiment_threeclass_prompt.txt` to forbid synonyms. Across re-runs
  the violation count moved 8 -> 3 -> 5; the LLM deterministically re-emitted
  the two banned words on genuinely disappointing reviews, and rewording also
  drifted unrelated sentiment predictions run-to-run (111 -> 112 -> 113).
- **Resolution (chosen by user): constrained decoding.** The course endpoint
  supports `response_format` with a JSON schema and enums (OpenAI structured
  outputs style). We switched the prompt's response format to a single JSON
  object and send
  `response_format={"type":"json_schema", "json_schema":{schema with sentiment
  enum {POSITIVE,NEUTRAL,NEGATIVE} and emotion enum {the 8}}}`. This enforces
  valid labels at decode time. Final run: 0 format violations — all 150
  sentiment in the 3 classes and all 150 emotion in the 8.
- **Note on history:** the earlier runs and their violation counts are kept in
  `outputs/step6_results.json` under settings.run_history (the parsed emotion
  value there shows None for violations; the raw banned labels
  disappointment/frustration are documented here). No output was ever silently
  remapped.
- **Metrics drift from the fix:** final overall accuracy is 76.0% (114/150),
  and only a handful of sentiment predictions differ from the original run
  (e.g. 3 differ from the immediately-prior run). The final numbers below are
  the authoritative ones.

## 8. Balanced three-class run key finding (Step 6)

- Imbalanced first-100 run (93 POSITIVE / 7 NEGATIVE, Step 2 binary) looked
  near-perfect (97%). The balanced 150 (50/50/50 incl. NEUTRAL) drops to 74%
  overall: POSITIVE 88%, NEGATIVE 96%, NEUTRAL only 38%.
- 3-star NEUTRAL reviews are largely NOT recognized as their own class: of 50,
  only 19 (38%) predicted NEUTRAL; 26 (52%) collapse into NEGATIVE and 5 (10%)
  into POSITIVE.
- So the balanced run reveals the model is much weaker than the lopsided run
  suggested, and 3-star reviews mostly read as negative rather than neutral.
