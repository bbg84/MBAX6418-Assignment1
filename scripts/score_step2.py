#!/usr/bin/env python3
"""Step 2 — score the first 100 Gift Cards reviews against the rating.

Sends only title+text to the course endpoint (thinking disabled), derives the
correct label from the rating AFTER the model call (4-5=POSITIVE, 1-3=NEGATIVE),
and writes a reproducible results file. The model never sees the rating.
"""
import gzip, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "Gift_Cards.jsonl.gz")
PROMPT_FILE = os.path.join(ROOT, "prompts", "sentiment_prompt.txt")
OUT_FILE = os.path.join(ROOT, "outputs", "step2_results.json")
ENV_FILE = os.path.join(ROOT, ".env")

N_ROWS = 100
THRESHOLD = 4.0  # rating >= 4 -> POSITIVE, else NEGATIVE (binary, Step 2)

# --- config ---
cfg = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        cfg[k] = v

BASE_URL = cfg["OPENAI_BASE_URL"].rstrip("/")
API_KEY = cfg["OPENAI_API_KEY"]
MODEL = cfg["CLASSIFICATION_MODEL"]

# settings fixed for reproducibility
SETTINGS = {
    "data_file": "data/Gift_Cards.jsonl.gz",
    "batch_definition": "first 100 reviews in dataset order (no sampling, no shuffle)",
    "n_rows": N_ROWS,
    "prompt_file": "prompts/sentiment_prompt.txt",
    "endpoint_base_url": BASE_URL,
    "model": MODEL,
    "temperature": 0,
    "max_tokens": 8,
    "chat_template_kwargs": {"enable_thinking": False},
    "correct_label_rule": "rating >= 4.0 -> POSITIVE, else NEGATIVE",
    "model_input_fields": ["title", "text"],  # rating deliberately excluded
    "saved_passthrough_fields": ["title", "text", "rating", "verified_purchase",
                                 "helpful_vote", "timestamp", "asin"],
}


def classify(title, text):
    prompt = open(PROMPT_FILE).read().replace("{title}", title).replace("{text}", text)
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": SETTINGS["max_tokens"],
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        BASE_URL + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    rows = []
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= N_ROWS:
                break
            rows.append(json.loads(line))
    assert len(rows) == N_ROWS, f"expected {N_ROWS} rows, got {len(rows)}"

    results = []
    for idx, r in enumerate(rows):
        title = r.get("title") or ""
        text = r.get("text") or ""
        pred = classify(title, text)
        rating = r.get("rating")
        correct_label = "POSITIVE" if rating >= THRESHOLD else "NEGATIVE"
        matched = pred == correct_label
        rec = {
            "row_index": idx,
            "title": title,
            "text": text,
            "rating": rating,
            "verified_purchase": r.get("verified_purchase"),
            "helpful_vote": r.get("helpful_vote"),
            "timestamp": r.get("timestamp"),
            "asin": r.get("asin"),
            "model_prediction": pred,
            "correct_label": correct_label,
            "matched": matched,
        }
        results.append(rec)
        print(f"[{idx+1:3d}/{N_ROWS}] pred={pred:<8} correct={correct_label:<8} matched={matched}")

    payload = {
        "settings": SETTINGS,
        "results": results,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nWROTE {OUT_FILE}")


if __name__ == "__main__":
    main()
