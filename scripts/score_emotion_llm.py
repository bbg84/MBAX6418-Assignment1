#!/usr/bin/env python3
"""Step 5 (part 1) — run the extended prompt on the same first 100 reviews.

For each review sends only title+text to the course endpoint (thinking
disabled), parses SENTIMENT + EMOTION, and flags any sentiment change versus the
Step 2 run. Rating is never sent.
"""
import gzip, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV_FILE = os.path.join(ROOT, ".env")
STEP2 = os.path.join(ROOT, "outputs", "step2_results.json")
PROMPT_FILE = os.path.join(ROOT, "prompts", "sentiment_emotion_prompt.txt")
OUT_RAW = os.path.join(ROOT, "outputs", "step5_llm_raw.json")

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
    "prompt_file": "prompts/sentiment_emotion_prompt.txt",
    "model": MODEL,
    "temperature": 0,
    "max_tokens": 16,
    "chat_template_kwargs": {"enable_thinking": False},
    "output_format": "exactly two lines: SENTIMENT: POSITIVE|NEGATIVE then EMOTION: <one of 8>",
    "emotions": EMOTIONS,
    "batch": "same first 100 reviews as Step 2 (dataset order)",
    "model_input_fields": ["title", "text"],
}


def classify(title, text):
    prompt = open(PROMPT_FILE).read().replace("{title}", title).replace("{text}", text)
    body = {"model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": SETTINGS["max_tokens"],
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(BASE_URL + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def parse(raw):
    s = re.search(r"SENTIMENT\s*[:=]\s*(POSITIVE|NEGATIVE)", raw)
    e = re.search(r"EMOTION\s*[:=]\s*(" + "|".join(EMOTIONS) + r")\b", raw, re.IGNORECASE)
    sentiment = s.group(1).upper() if s else None
    emotion = e.group(1).lower() if e else None
    return sentiment, emotion


def main():
    step2 = json.load(open(STEP2))
    rows = step2["results"]
    assert len(rows) == 100

    out = []
    for r in rows:
        raw = classify(r["title"], r["text"])
        sentiment, emotion = parse(raw)
        sentiment_changed = (sentiment is None) or (sentiment != r["model_prediction"])
        out.append({
            "row_index": r["row_index"],
            "title": r["title"],
            "text": r["text"],
            "rating": r["rating"],
            "step2_sentiment": r["model_prediction"],
            "llm_sentiment": sentiment,
            "sentiment_changed": sentiment_changed,
            "emotion_llm": emotion,
            "raw": raw,
            "format_violation": sentiment is None or emotion is None,
        })
        print(f"[{r['row_index']+1:3d}] sent={sentiment!s:8} step2={r['model_prediction']:8} "
              f"emo={emotion!s:12} changed={sentiment_changed} viol={emotion is None or sentiment is None}")

    payload = {"settings": SETTINGS, "results": out}
    with open(OUT_RAW, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    changes = sum(1 for o in out if o["sentiment_changed"])
    viol = sum(1 for o in out if o["format_violation"])
    print(f"\nWROTE {OUT_RAW}")
    print(f"sentiment changes vs Step 2: {changes}/100 | format violations: {viol}/100")


if __name__ == "__main__":
    main()
