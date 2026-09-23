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
