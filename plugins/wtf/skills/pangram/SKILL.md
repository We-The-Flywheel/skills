---
name: pangram
version: 1.0.0
description: |
  Score text for AI-generated content using the Pangram Labs API. Submits text
  (or file content) to Pangram's detection endpoint and returns: overall AI
  fraction (0–100%), prediction label, and any sentence-level highlights.
  Use before publishing content to verify it passes the AI-detection bar.
  Requires PANGRAM_API_KEY in ~/.env.shared.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Pangram AI Detection Scorer

Submit text to the Pangram Labs API and get back an AI-content score.

## API facts

- **Endpoint:** `POST https://text.external-api.pangram.com/task`
- **Auth header:** `x-api-key: <key>`
- **Response:** async — returns a `task_id`; poll `GET https://text.external-api.pangram.com/task/<id>` until `stage == "STAGE_SUCCESS"`
- **Key fields:** `fraction_ai` (0.0–1.0), `fraction_ai_assisted`, `prediction`, `prediction_short`
- **Cost:** $0.05 per 1,000 words (real-time); minimum $5 top-up
- **Key location (OpenBao):** `secret/ops-shared/integrations/pangram` → field `api_key`

## Your task

1. **Get the text to score.**
   - If the user supplied a file path, read it with the Read tool.
   - If they pasted text directly, use that.
   - If neither, ask with AskUserQuestion.

2. **Load the API key from OpenBao.**

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   PANGRAM_API_KEY=$(bao kv get -field=api_key secret/ops-shared/integrations/pangram 2>/dev/null)
   echo "${PANGRAM_API_KEY:-NOT_SET}"
   ```

   If `NOT_SET`, stop and tell the user the key is at `secret/ops-shared/integrations/pangram` in OpenBao and may need to be added.

3. **Submit the task.**

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   PANGRAM_API_KEY=$(bao kv get -field=api_key secret/ops-shared/integrations/pangram)
   RESPONSE=$(curl -fsS -X POST \
     -H "x-api-key: $PANGRAM_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{\"text\": $(echo "$TEXT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
     "https://text.external-api.pangram.com/task")
   echo "$RESPONSE"
   ```

   Extract `task_id` from the response JSON.

4. **Poll until done** (max 30s, 2s interval).

   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   PANGRAM_API_KEY=$(bao kv get -field=api_key secret/ops-shared/integrations/pangram)
   for i in $(seq 1 15); do
     RESULT=$(curl -fsS \
       -H "x-api-key: $PANGRAM_API_KEY" \
       "https://text.external-api.pangram.com/task/$TASK_ID")
     STAGE=$(echo "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("stage",""))')
     if [ "$STAGE" = "STAGE_SUCCESS" ] || [ "$STAGE" = "STAGE_FAILED" ]; then
       echo "$RESULT"
       break
     fi
     sleep 2
   done
   ```

5. **Parse and present results.**

   Extract and display:
   - `fraction_ai` → percentage, e.g. "38% AI"
   - `fraction_ai_assisted` → e.g. "12% AI-assisted"
   - `prediction` (full label) + `prediction_short`
   - Word count (for cost transparency: `words / 1000 × $0.05`)

6. **Interpret the score.**

   | Score | Pangram label | Interpretation |
   |-------|--------------|----------------|
   | 0–20% | Likely human | Passes cleanly |
   | 20–40% | Unclear | Borderline — humanize further |
   | 40–70% | Likely AI-assisted | Needs work before publishing |
   | 70–100% | Likely AI | Significant humanization required |

   Give a one-line recommendation: pass / humanize + re-run / major rewrite needed.

## Example output

```
📊 Pangram AI Detection Score
──────────────────────────────
AI content:          38%  (fraction_ai: 0.38)
AI-assisted:         12%  (fraction_ai_assisted: 0.12)
Prediction:          Unclear — may contain AI content
Words scanned:       847  (~$0.04 this call)

Verdict: Borderline. Run /humanizer on the flagged sections, then re-score.
```

## Error handling

- **401:** bad or missing API key — check OpenBao at `secret/ops-shared/integrations/pangram`
- **402 / payment required:** out of credits — top up at pangram.com/billing
- **STAGE_FAILED:** Pangram rejected the text (too short < ~50 words, or unsupported characters)
- **Timeout (15 polls):** unlikely but retry once; if persistent, the task may be stuck

## Notes

- Minimum scoreable text is ~50 words; shorter inputs return `STAGE_FAILED`
- The API key lives in OpenBao at `secret/ops-shared/integrations/pangram` field `api_key`
- For batch scoring of multiple files, call the skill per file and aggregate
- Re-running the humanizer skill and re-scoring is the intended workflow for iterative content improvement
