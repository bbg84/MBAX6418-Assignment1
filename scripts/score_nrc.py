#!/usr/bin/env python3
"""Step 5 (part 2) — derive a primary emotion with the NRC emotion word list.

Completely independent of the LLM: scores each review's title+text words against
the NRC Emotion Lexicon (8 emotions), sums the associations per emotion, applies
the fixed tie-priority rule, and assigns NONE when all scores are zero.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEXICON = os.path.join(ROOT, "data", "nrc", "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt")
STEP2 = os.path.join(ROOT, "outputs", "step2_results.json")
OUT = os.path.join(ROOT, "outputs", "step5_nrc_raw.json")

EMOTIONS = ["anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust"]
# Fixed tie-break priority, order as listed in the assignment
TIE_PRIORITY = EMOTIONS

LEXICON_SOURCE = ("NRC Emotion Lexicon (NRC-Emotion-Lexicon-Wordlevel-v0.92.txt), "
                  "S. Mohammad, https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm "
                  "(canonical download NRC-Emotion-Lexicon.zip)")

SETTINGS = {
    "lexicon_source": LEXICON_SOURCE,
    "emotions": EMOTIONS,
    "tie_rule": f"fixed deterministic priority order: {' -> '.join(TIE_PRIORITY)}",
    "none_rule": "if all emotion scores are zero, assign NONE",
    "tokenization": "lowercase; split on non-alphanumeric; keep tokens containing letters",
    "scored_text": "title + text combined",
    "lexicon_value": "binary association (0/1) per word-emotion; sum counts per emotion",
}


def load_lexicon(path):
    w2e = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            word, emotion, val = parts
            if emotion not in EMOTIONS or val != "1":
                continue
            w2e.setdefault(word, set()).add(emotion)
    return w2e


def score_text(text, w2e):
    counts = {e: 0 for e in EMOTIONS}
    for tok in re.split(r"[^A-Za-z0-9]+", text.lower()):
        if not re.search(r"[A-Za-z]", tok):
            continue
        for e in w2e.get(tok, ()):
            counts[e] += 1
    return counts


def primary(counts):
    total = sum(counts.values())
    if total == 0:
        return "NONE"
    top = max(counts.values())
    candidates = [e for e in EMOTIONS if counts[e] == top]  # already in TIE_PRIORITY order
    return candidates[0]


def main():
    w2e = load_lexicon(LEXICON)
    print(f"lexicon loaded: {len(w2e)} words mapped across {len(EMOTIONS)} emotions")
    step2 = json.load(open(STEP2))["results"]

    out = []
    for r in step2:
        counts = score_text((r["title"] or "") + " " + (r["text"] or ""), w2e)
        emotion = primary(counts)
        out.append({**{"row_index": r["row_index"], "title": r["title"], "text": r["text"]},
                    "scores": counts, "emotion_nrc": emotion})
        print(f"[{r['row_index']+1:3d}] nrc={emotion:<10} scores={counts}")

    payload = {"settings": SETTINGS, "results": out}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nWROTE {OUT}")


if __name__ == "__main__":
    main()
