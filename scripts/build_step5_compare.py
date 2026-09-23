#!/usr/bin/env python3
"""Step 5 (part 3) — merge the two independent emotion methods, write the
combined results file, and print the comparison report.
"""
import json, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM = os.path.join(ROOT, "outputs", "step5_llm_raw.json")
NRC = os.path.join(ROOT, "outputs", "step5_nrc_raw.json")
STEP2 = os.path.join(ROOT, "outputs", "step2_results.json")
OUT = os.path.join(ROOT, "outputs", "step5_results.json")

llm_data = json.load(open(LLM))
nrc_data = json.load(open(NRC))
step2 = json.load(open(STEP2))["results"]

llm, nrc = llm_data["results"], nrc_data["results"]
nrc_by_idx = {r["row_index"]: r for r in nrc}
llm_by_idx = {r["row_index"]: r for r in llm}

rows = []
for s2 in step2:
    i = s2["row_index"]
    L = llm_by_idx[i]
    N = nrc_by_idx[i]
    rows.append({
        "row_index": i, "title": s2["title"], "text": s2["text"], "rating": s2["rating"],
        "sentiment_step2": s2["model_prediction"],
        "sentiment_llm": L["llm_sentiment"],
        "sentiment_changed_vs_step2": L["sentiment_changed"],
        "emotion_llm": L["emotion_llm"],
        "emotion_nrc": N["emotion_nrc"],
        "nrc_scores": N["scores"],
    })

payload = {
    "settings": {
        "llm_settings": llm_data["settings"],
        "nrc_settings": nrc_data["settings"],
        "independence": ("emotion_llm comes from the endpoint prompt; emotion_nrc comes "
                         "from the word list only; neither influences the other"),
        "comparison_rule": "agree==True when emotion_llm == emotion_nrc (same 8 labels; NONE is its own label)",
    },
    "results": rows,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("WROTE", OUT)


def dist(key):
    return dict(sorted(Counter(r[key] for r in rows).items()))


agree = [r for r in rows if r["emotion_llm"] == r["emotion_nrc"]]
N = len(rows)
print(f"\n=== STEP 5 comparison ({N} reviews) ===")
print(f"same primary emotion (agree): {len(agree)}/{N} = {len(agree)/N*100:.1f}%")
print(f"NRC results that were NONE:  {sum(1 for r in rows if r['emotion_nrc']=='NONE')}")
print(f"\nLLM emotion distribution:  {dist('emotion_llm')}")
print(f"NRC emotion distribution:  {dist('emotion_nrc')}")

# disagreement types: top (llm, nrc) pairs among mismatches
mismatch = [r for r in rows if r["emotion_llm"] != r["emotion_nrc"]]
pairs = Counter((r["emotion_llm"], r["emotion_nrc"]) for r in mismatch)
print(f"\nDisagreement types (LLM -> NRC), most common first:")
for (a, b), c in pairs.most_common():
    print(f"  {a:>12} -> {b:<12} x{c}")

# sentiment drift
changed = [r for r in rows if r["sentiment_changed_vs_step2"]]
print(f"\nSentiment changed vs Step 2: {len(changed)}")
for r in changed:
    print(f"  [{r['row_index']}] step2={r['sentiment_step2']} new={r['sentiment_llm']} | {r['title']!r} | {r['text'][:80]!r}")

# example disagreements to aid the narrative: a few concrete rows
print("\nExample reviews that explain divergence (LLM != NRC):")
shown = 0
for r in mismatch:
    if shown >= 8:
        break
    print(f"  [{r['row_index']}] LLM:{r['emotion_llm']} NRC:{r['emotion_nrc']} | nrc_scores={r['nrc_scores']}")
    print(f"      title: {r['title']!r}")
    print(f"      text:  {r['text'][:110]!r}")
    shown += 1
