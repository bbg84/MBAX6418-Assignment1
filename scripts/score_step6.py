#!/usr/bin/env python3
"""Step 6 (part 2) — three-class balanced scoring of the 150-review sample.

Sends title+text only (never the rating), extended prompt for POSITIVE/NEUTRAL/
NEGATIVE + 8-emotion output. Derives the correct label from the rating AFTER
prediction (4-5 POSITIVE, 3 NEUTRAL, 1-2 NEGATIVE). Saves complete results and
prints accuracy + confusion matrix.
"""
import json, os, re, urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV_FILE = os.path.join(ROOT, ".env")
SAMPLE = os.path.join(ROOT, "outputs", "step6_sample.json")
PROMPT_FILE = os.path.join(ROOT, "prompts", "sentiment_threeclass_prompt.txt")
OUT = os.path.join(ROOT, "outputs", "step6_results.json")

EMOTIONS = ["anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust"]

cfg = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        cfg[k] = v
BASE_URL = cfg["OPENAI_BASE_URL"].rstrip("/")
API_KEY = cfg["OPENAI_API_KEY"]
MODEL = cfg["CLASSIFICATION_MODEL"]

SETTINGS = {
    "prompt_file": "prompts/sentiment_threeclass_prompt.txt",
    "sample_file": "outputs/step6_sample.json",
    "model": MODEL,
    "temperature": 0,
    "max_tokens": 40,
    "chat_template_kwargs": {"enable_thinking": False},
    "constrained_decoding": ("response_format json_schema with enums: sentiment in "
                             "{POSITIVE,NEUTRAL,NEGATIVE}; emotion in the approved 8. "
                             "Decided by user to guarantee the 8-label emotion rule."),
    "sentiment_classes": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
    "emotions": EMOTIONS,
    "correct_label_rule": "rating 4-5 -> POSITIVE; rating 3 -> NEUTRAL; rating 1-2 -> NEGATIVE (after prediction only)",
    "model_input_fields": ["title", "text"],
}

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"]},
        "emotion": {"type": "string", "enum": EMOTIONS},
    },
    "required": ["sentiment", "emotion"],
    "additionalProperties": False,
}


def classify(title, text):
    prompt = open(PROMPT_FILE).read().replace("{title}", title).replace("{text}", text)
    body = {"model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": SETTINGS["max_tokens"],
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "review_classification", "schema": JSON_SCHEMA}}}
    req = urllib.request.Request(BASE_URL + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def parse(raw):
    try:
        obj = json.loads(raw)
        sentiment = obj.get("sentiment")
        emotion = obj.get("emotion", "").lower()
        if emotion not in EMOTIONS:
            emotion = None
        if sentiment not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            sentiment = None
        return sentiment, emotion
    except Exception:
        return None, None


def correct_label(rating):
    if rating >= 4.0:
        return "POSITIVE"
    if rating == 3.0:
        return "NEUTRAL"
    return "NEGATIVE"


def main():
    sample = json.load(open(SAMPLE))
    rows = sample["sample"]
    assert len(rows) == 150

    results = []
    for i, r in enumerate(rows):
        raw = classify(r["title"], r["text"])
        sentiment, emotion = parse(raw)
        correct = correct_label(r["rating"])
        results.append({
            "ordinal": r["ordinal"],
            "title": r["title"],
            "text": r["text"],
            "rating": r["rating"],
            "verified_purchase": r.get("verified_purchase"),
            "helpful_vote": r.get("helpful_vote"),
            "timestamp": r.get("timestamp"),
            "asin": r.get("asin"),
            "correct_label": correct,
            "prediction": sentiment,
            "correct": sentiment == correct,
            "emotion_llm": emotion,
            "format_violation": sentiment is None or emotion is None,
            "raw": raw,
        })
        print(f"[{i+1:3d}] gold={correct:<8} pred={str(sentiment):<8} match={sentiment==correct} emo={emotion}")

    prior = None
    previous_files = []
    if os.path.exists(OUT):
        try:
            pd = json.load(open(OUT))
            prior_invalid = [(r["ordinal"], r["emotion_llm"]) for r in pd.get("results", []) if r.get("format_violation")]
            # accumulate persistent run history (each superseded run)
            prior_history = (pd.get("settings", {}).get("run_history") or [])
            preceding = {
                "run_info": pd.get("settings", {}).get("run_history_label", "earlier run"),
                "format_violation_count": len(prior_invalid),
                "invalid_emotion_labels": [e for _, e in prior_invalid],
                "invalid_ordinals": [o for o, _ in prior_invalid],
                "sentiment_before": {r["ordinal"]: r.get("prediction") for r in pd.get("results", [])},
            }
            previous_files = prior_history + [preceding]
            prior = {
                "superseded": True,
                "why": "corrected prompt run(s) supersede earlier runs with emotion labels outside the approved set",
                "run_history": previous_files,
            }
        except Exception:
            prior = None

    payload = {"settings": {**SETTINGS, **{"sample_settings": sample["settings"]},
                            **({"prior_run": prior} if prior else {}),
                            **({"run_history": previous_files} if previous_files else {})},
               "results": results}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("\nWROTE", OUT)

    # ---- analysis ----
    N = len(results)
    n_correct = sum(1 for r in results if r["correct"])
    viol = sum(1 for r in results if r["format_violation"])
    print(f"\n=== STEP 6 three-class (N={N}) ===")
    print(f"overall accuracy: {n_correct}/{N} = {n_correct/N*100:.1f}% | correct={n_correct} incorrect={N-n_correct} format_violations={viol}")

    classes = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    print("per-class accuracy:")
    for c in classes:
        sub = [r for r in results if r["correct_label"] == c]
        ok = [r for r in sub if r["correct"]]
        print(f"  {c:<8}: {len(ok)}/{len(sub)} = {len(ok)/len(sub)*100:.1f}%")

    print("confusion matrix (rows=correct, cols=predicted):")
    print(f"{'':>12}" + "".join(f"{c:>12}" for c in classes))
    for c in classes:
        sub = [r for r in results if r["correct_label"] == c]
        row = {k: sum(1 for r in sub if r["prediction"] == k) for k in classes}
        print(f"{c:>12}" + "".join(f"{row[k]:>12}" for k in classes))

    neut = [r for r in results if r["correct_label"] == "NEUTRAL"]
    n = len(neut)
    print(f"\n3-star NEUTRAL breakdown (n={n}):")
    for p in classes:
        cnt = sum(1 for r in neut if r["prediction"] == p)
        print(f"  predicted {p:<8}: {cnt}  ({cnt/n*100:.1f}%)")


if __name__ == "__main__":
    main()
