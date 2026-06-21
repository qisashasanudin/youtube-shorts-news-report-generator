---
name: local-llm-orchestration
description: "Run local LLM-backed workflows: launch Ollama, choose models by hardware, call /api/generate from Python, and wire offline generation into local pipelines."
platforms: [windows]
---

# Local LLM Orchestration

USE THIS when the user wants a standalone, offline language model step inside a local pipeline instead of remote/API completion, especially when the host has enough CPU/RAM/GPU for a small-to-mid open model.

## Hardware fit guidelines

- 8–16 GB RAM + any GPU: start with 4B-class dense or MoE models for response speed.
- 16+ GB RAM + dedicated GPU: 12B–31B class is usable but expect higher latency.
- Prefer smaller quantized variants when throughput matters more than peak quality.

## Setup sequence

1. Install Ollama on the host if absent.
2. Pull the chosen model tag: `ollama pull <model>[:variant]`
3. Start the daemon and confirm health: `ollama serve` not needed; `ollama ps` can confirm loaded models.

## Model recommendations

- `gemma4:4b` — strong for short structured outputs
- `gemma4` — default when resources allow
- Other options to consider by context: `qwen2.5:7b`, `llama3.1:8b`, `mistral:7b`

## HTTP API contract

Ollama exposes:
- `POST http://localhost:11434/api/generate`
- Body: `{"model":"...","prompt":"...","stream":false}`
- Response: `{"response":"...","done":true}`

Call from Python or shell; sample Python pattern:
```
requests.post("http://localhost:11434/api/generate", json={"model":"...", "prompt":"...", "stream":False}, timeout=120)
```

## Integration rules

- Do not hardcode the model name in downstream skill logic without the user's explicit selection.
- Always time out the request and surface generation failures clearly instead of silent fallbacks.
- When the pipeline should still run without the model, design it to require explicit manual input as fallback.

## Pitfalls

- Do not assert the Ollama binary is on PATH; locate it if needed, but do not record PATH failures as durable constraints.
- Avoid extremely long prompts on the first call; shorter constrained tasks reveal model availability faster.
- Windows firewall rules can block local inbound if misconfigured; confirm localhost HTTP before diagnosing model issues.

## Support files

- `references/ollama-http-generate.md` — request/response schema and common shell snippets.