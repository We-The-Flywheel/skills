#!/usr/bin/env python3
"""
Multi-LLM Deliberation — self-contained, no backend needed.
Calls OpenRouter API directly for a 3-stage consensus process.

Stage 1: Diverge — 5 models answer independently
Stage 2: Rank   — each model ranks the other responses
Stage 3: Synthesize — best synthesizer creates consensus
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Auto-load key from .env.shared if not in environment
if not API_KEY:
    for envfile in [
        os.path.expanduser("~/.env.shared"),
    ]:
        if os.path.isfile(envfile):
            with open(envfile) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                        break
            if API_KEY:
                break

MODELS = {
    "gemini-lite": "google/gemini-3.1-flash-lite",
    "gpt": "openai/gpt-4.1-mini",
    "deepseek": "deepseek/deepseek-chat-v3-0324",
    "mistral": "mistralai/mistral-small-3.1-24b-instruct",
    "llama": "meta-llama/llama-3.3-70b-instruct",
}

SYNTHESIZER = "google/gemini-3-flash-preview"


def emit_progress(event: str, **data):
    """Emit a structured progress event to stderr as a single-line JSON object.
    Wrappers that want to stream progress (e.g. an SSE bridge or TUI) can parse
    stderr line-by-line; everyone else can ignore it."""
    print(json.dumps({"event": event, **data}), file=sys.stderr, flush=True)


def chat(model: str, messages: list[dict], temperature: float = 0.7) -> dict:
    """Single OpenRouter chat completion. Returns {content, usage, model}."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/We-The-Flywheel/skills",
            "X-Title": "multi-llm-deliberation",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 402:
            print(f"\nERROR: OpenRouter has no credits remaining.", file=sys.stderr)
            print(f"Top up at https://openrouter.ai/settings/credits", file=sys.stderr)
            sys.exit(2)
        elif e.code == 401:
            print(f"\nERROR: OpenRouter API key is invalid or expired.", file=sys.stderr)
            sys.exit(2)
        else:
            # Non-fatal: raise so caller can skip this model
            raise RuntimeError(f"OpenRouter HTTP {e.code} for {model}: {body[:200]}")
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"Unexpected response from {model}: {json.dumps(data)[:300]}")
    content = data["choices"][0]["message"].get("content")
    if not content:
        raise RuntimeError(f"Null/empty content from {model}")
    usage = data.get("usage", {})
    return {
        "content": content,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        },
        "model": model,
    }


def stage1_diverge(question: str, temperature: float = 0.7) -> tuple[dict[str, str], list[dict]]:
    """All models answer the question independently in parallel.
    Returns (responses dict, model_results list)."""
    prompt = [{"role": "user", "content": question}]
    results = {}
    model_results = []

    def ask(name: str, model: str) -> tuple[str, dict]:
        return name, chat(model, prompt, temperature=temperature)

    with ThreadPoolExecutor(max_workers=len(MODELS)) as pool:
        futures = {pool.submit(ask, n, m): n for n, m in MODELS.items()}
        for future in as_completed(futures):
            model_name = futures[future]
            try:
                name, result = future.result()
                results[name] = result["content"]
                model_results.append({
                    "name": name,
                    "modelId": MODELS[name],
                    "status": "success",
                    "inputTokens": result["usage"]["prompt_tokens"],
                    "outputTokens": result["usage"]["completion_tokens"],
                })
                emit_progress("model_done", stage="diverge", model=name, status="success")
            except Exception as e:
                print(f"\n  ⚠ {model_name} failed: {e}", file=sys.stderr)
                model_results.append({
                    "name": model_name,
                    "modelId": MODELS[model_name],
                    "status": "error",
                    "error": str(e),
                    "inputTokens": 0,
                    "outputTokens": 0,
                })
                emit_progress("model_done", stage="diverge", model=model_name, status="error")
    if not results:
        print("\nERROR: All models failed.", file=sys.stderr)
        sys.exit(2)
    return results, model_results


def stage2_rank(question: str, responses: dict[str, str]) -> tuple[dict[str, list], list[dict]]:
    """Each model ranks the anonymous responses. Returns (rankings, model_results)."""
    # Build anonymous response list
    labels = list(responses.keys())
    response_block = "\n\n".join(
        f"--- Response {chr(65 + i)} ---\n{responses[name]}"
        for i, name in enumerate(labels)
    )

    ranking_prompt = f"""You are evaluating responses to this question:

"{question}"

Here are the responses:

{response_block}

Rank these responses from best to worst. Consider accuracy, completeness, clarity, and usefulness.
Reply with ONLY a JSON array of letters in order from best to worst, e.g. ["B", "A", "D", "C"]"""

    rankings = {}
    model_results = []

    def rank(name: str, model: str) -> tuple[str, list, dict]:
        result = chat(model, [{"role": "user", "content": ranking_prompt}], temperature=0.3)
        raw = result["content"] or ""
        usage = result["usage"]
        def _valid_ranking(parsed: list) -> bool:
            return isinstance(parsed, list) and all(isinstance(x, str) for x in parsed)

        # Extract JSON array from response
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("["):
                try:
                    parsed = json.loads(line)
                    if _valid_ranking(parsed):
                        return name, parsed, usage
                except json.JSONDecodeError:
                    pass
        # Fallback: try to find array anywhere in response
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start:end + 1])
                if _valid_ranking(parsed):
                    return name, parsed, usage
            except json.JSONDecodeError:
                pass
        return name, [chr(65 + i) for i in range(len(responses))], usage  # fallback

    # Only use models that succeeded in stage 1
    rank_models = {n: m for n, m in MODELS.items() if n in responses}
    with ThreadPoolExecutor(max_workers=len(MODELS)) as pool:
        futures = {pool.submit(rank, n, m): n for n, m in rank_models.items()}
        for future in as_completed(futures):
            model_name = futures[future]
            try:
                name, ranking, usage = future.result()
                rankings[name] = ranking
                model_results.append({
                    "name": name,
                    "modelId": MODELS[name],
                    "status": "success",
                    "inputTokens": usage["prompt_tokens"],
                    "outputTokens": usage["completion_tokens"],
                })
                emit_progress("model_done", stage="rank", model=name, status="success")
            except Exception as e:
                print(f"\n  ⚠ {model_name} ranking failed: {e}", file=sys.stderr)
                model_results.append({
                    "name": model_name,
                    "modelId": MODELS[model_name],
                    "status": "error",
                    "error": str(e),
                    "inputTokens": 0,
                    "outputTokens": 0,
                })
                emit_progress("model_done", stage="rank", model=model_name, status="error")

    return rankings, model_results


def compute_scores(rankings: dict[str, list], labels: list[str]) -> list[tuple[str, float]]:
    """Aggregate rankings into scores. Lower = better."""
    scores = {chr(65 + i): [] for i in range(len(labels))}
    for ranker, ranking in rankings.items():
        for position, letter in enumerate(ranking):
            letter = letter.upper()
            if letter in scores:
                scores[letter].append(position + 1)

    aggregated = []
    for i, name in enumerate(labels):
        letter = chr(65 + i)
        ranks = scores.get(letter, [])
        avg = sum(ranks) / len(ranks) if ranks else 99
        aggregated.append((name, avg))
    aggregated.sort(key=lambda x: x[1])
    return aggregated


def stage3_synthesize(question: str, responses: dict[str, str], scored: list[tuple[str, float]]) -> tuple[str, dict]:
    """Synthesizer creates consensus. Returns (consensus_text, usage_dict)."""
    ranked_block = "\n\n".join(
        f"--- {name} (rank #{i+1}, avg score {score:.1f}) ---\n{responses[name]}"
        for i, (name, score) in enumerate(scored)
    )

    prompt = f"""You are synthesizing multiple AI perspectives into a single consensus answer.

Question: "{question}"

Here are the responses, ordered by peer ranking (best first):

{ranked_block}

Create a comprehensive consensus answer that:
1. Leads with the strongest points from top-ranked responses
2. Incorporates unique valid insights from all responses
3. Notes any significant disagreements between models
4. Provides a clear, actionable conclusion

Be concise but thorough. Do not mention the models by name or that this is a synthesis."""

    result = chat(SYNTHESIZER, [{"role": "user", "content": prompt}], temperature=0.5)
    return result["content"], result["usage"]


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    json_mode = "--json" in args
    if json_mode:
        args.remove("--json")

    temperature = 0.7
    if "--temperature" in args:
        idx = args.index("--temperature")
        try:
            temperature = float(args[idx + 1])
        except (IndexError, ValueError):
            print("Error: --temperature requires a numeric value", file=sys.stderr)
            sys.exit(1)
        del args[idx:idx + 2]

    question = " ".join(args) if args else ""
    if not question:
        print("Usage: council.py [--json] [--temperature 0.7] <question>", file=sys.stderr)
        sys.exit(1)

    total_start = time.time()

    if not json_mode:
        print(f"\n{'='*60}")
        print(f"  Multi-LLM Deliberation")
        print(f"  Question: {question}")
        print(f"{'='*60}\n")

    # Stage 1
    emit_progress("stage_start", stage="diverge", models=list(MODELS.keys()))
    if not json_mode:
        print("Stage 1: Diverge (5 models answering independently)...")
    s1_start = time.time()
    responses, s1_models = stage1_diverge(question, temperature=temperature)
    s1_duration = int((time.time() - s1_start) * 1000)
    emit_progress("stage_done", stage="diverge", duration_ms=s1_duration)
    labels = list(responses.keys())

    if not json_mode:
        for name, resp in responses.items():
            model_id = MODELS[name].split("/")[-1]
            print(f"\n--- {model_id} ---")
            print(resp.strip())

    # Stage 2
    emit_progress("stage_start", stage="rank", models=list(responses.keys()))
    if not json_mode:
        print(f"\n{'─'*60}")
        print("Stage 2: Rank (models peer-review anonymously)...")
    s2_start = time.time()
    rankings, s2_models = stage2_rank(question, responses)
    s2_duration = int((time.time() - s2_start) * 1000)
    emit_progress("stage_done", stage="rank", duration_ms=s2_duration)
    scored = compute_scores(rankings, labels)

    if not json_mode:
        print("\nPeer Rankings:")
        for i, (name, avg) in enumerate(scored, 1):
            model_id = MODELS[name].split("/")[-1]
            print(f"  {i}. {model_id} (avg rank: {avg:.1f})")

    # Stage 3
    emit_progress("stage_start", stage="synthesize", model=SYNTHESIZER)
    if not json_mode:
        print(f"\n{'─'*60}")
        print("Stage 3: Synthesize (creating consensus)...")
    s3_start = time.time()
    consensus, s3_usage = stage3_synthesize(question, responses, scored)
    s3_duration = int((time.time() - s3_start) * 1000)
    emit_progress("stage_done", stage="synthesize", duration_ms=s3_duration)

    total_duration = int((time.time() - total_start) * 1000)

    if json_mode:
        # Merge model results from all stages
        all_models = {}
        for m in s1_models:
            all_models[m["name"]] = {**m, "stages": ["diverge"]}
        for m in s2_models:
            name = m["name"]
            if name in all_models:
                all_models[name]["inputTokens"] += m["inputTokens"]
                all_models[name]["outputTokens"] += m["outputTokens"]
                all_models[name]["stages"].append("rank")
                if m["status"] == "error":
                    all_models[name]["status"] = "partial"
            else:
                all_models[name] = {**m, "stages": ["rank"]}

        output = {
            "models": list(all_models.values()),
            "synthesizer": {
                "modelId": SYNTHESIZER,
                "inputTokens": s3_usage["prompt_tokens"],
                "outputTokens": s3_usage["completion_tokens"],
            },
            "stages": {
                "diverge": {"durationMs": s1_duration, "models": [m["name"] for m in s1_models if m["status"] == "success"]},
                "rank": {"durationMs": s2_duration, "models": [m["name"] for m in s2_models if m["status"] == "success"]},
                "synthesize": {"durationMs": s3_duration, "model": SYNTHESIZER},
            },
            "totalDurationMs": total_duration,
            "consensus": consensus.strip(),
        }
        print(json.dumps(output))
    else:
        print(f"\n{'='*60}")
        print("  CONSENSUS ANSWER")
        print(f"{'='*60}\n")
        print(consensus.strip())
        print(f"\n{'='*60}")
        print(f"  Models: {len(responses)}/{len(MODELS)} responded")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
