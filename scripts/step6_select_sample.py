#!/usr/bin/env python3
"""Step 6 (part 1) — select a balanced three-class sample of 150 reviews.

50 POSITIVE (rating 4-5), 50 NEUTRAL (rating 3), 50 NEGATIVE (rating 1-2),
picked from the WHOLE Gift Cards file with a fixed random seed so the exact
sample is reproducible. Saves the sample with full metadata + reproducibility
record (seed, class counts, source ordinals).
"""
import gzip, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "Gift_Cards.jsonl.gz")
OUT = os.path.join(ROOT, "outputs", "step6_sample.json")

SEED = 6418
PER_CLASS = 50
CLASSES = {"POSITIVE": ["4.0", "5.0"], "NEUTRAL": ["3.0"], "NEGATIVE": ["1.0", "2.0"]}
KEEP_FIELDS = ["title", "text", "rating", "verified_purchase", "helpful_vote", "timestamp", "asin"]

def correct_label(rating):
    if rating >= 4.0:
        return "POSITIVE"
    if rating == 3.0:
        return "NEUTRAL"
    return "NEGATIVE"

def main():
    buckets = {"POSITIVE": [], "NEUTRAL": [], "NEGATIVE": []}
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for ordinal, line in enumerate(f):
            r = json.loads(line)
            lab = correct_label(r["rating"])
            buckets[lab].append({"ordinal": ordinal, "record": r})

    print("class totals in whole file:", {k: len(v) for k, v in buckets.items()})

    rng = random.Random(SEED)
    chosen = []
    for lab in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        pool = buckets[lab]
        picks = rng.sample(pool, PER_CLASS)
        print(f"  sampled {len(picks)} {lab} (seed={SEED})")
        for p in picks:
            rec = p["record"]
            chosen.append({
                "ordinal": p["ordinal"],
                "correct_label": lab,
                **{k: rec.get(k) for k in KEEP_FIELDS},
            })

    payload = {
        "settings": {
            "data_file": "data/Gift_Cards.jsonl.gz",
            "seed": SEED,
            "per_class": PER_CLASS,
            "class_sizes": {"POSITIVE": PER_CLASS, "NEUTRAL": PER_CLASS, "NEGATIVE": PER_CLASS},
            "class_def_from_rating": {"POSITIVE": "rating 4-5", "NEUTRAL": "rating 3", "NEGATIVE": "rating 1-2"},
            "sampling": f"balanced random sample from whole file, fixed seed {SEED}",
            "saved_fields": KEEP_FIELDS,
        },
        "sample": chosen,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    from collections import Counter
    print("selected:", dict(Counter(c["correct_label"] for c in chosen)), "total:", len(chosen))
    # reproducibility sanity: re-derive and confirm same ordinals
    re_pick = {}
    rng2 = random.Random(SEED)
    for lab in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        p2 = rng2.sample(buckets[lab], PER_CLASS)
        re_pick[lab] = sorted(p["ordinal"] for p in p2)
    ok = all(sorted(c["ordinal"] for c in chosen if c["correct_label"] == lab) == re_pick[lab] for lab in re_pick)
    print("reproducibility check (re-sampling with same seed matches):", ok)
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
