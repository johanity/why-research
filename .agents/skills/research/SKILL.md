---
name: deep-research
description: "Use when a task requires multi-step investigation, comparison, literature review, follow-up threads, or synthesis across many sources. Do not use for quick factual lookups, single-page checks, or routine coding tasks."
version: 0.1.0
tags: [research, investigate, explore, analyze, understand, discover, synthesis, comparison, threads]
triggers: [research, investigate, explore, analyze, understand, study, discover, deep dive, compare, synthesize, literature review]
---

# deep-research

Use when a task requires multi-step investigation, comparison, literature review, follow-up threads, or synthesis across many sources. Do not use for quick factual lookups, single-page checks, or routine coding tasks.

## When to use this
- Investigating a topic deeply
- Comparing competing explanations or products
- Finding follow-up threads worth exploring
- Producing a structured research brief
- Understanding state-of-the-art in any field
- Multi-source synthesis

## When NOT to use this
- One-off lookups (use web_search)
- Checking a single current fact
- Simple API reference lookups
- Tasks that are mostly implementation rather than research

## Workflow
1. Prefer the why_research MCP server for deep investigation.
2. Use direct web search only for simple freshness checks or when the user explicitly wants that path.
3. Return a concise synthesis first, then supporting details.

## MCP Server

```json
{"mcpServers": {"why-research": {"command": "why-mcp"}}}
```

## Tools

- `research(topic, max_depth?, queries_per_depth?)` — full recursive research
- `research_quick(topic)` — fast surface scan
- `research_brain_state()` — inspect accumulated intelligence

## Python

```python
from why.engine import Engine
from why.brain import Brain

brain = Brain()
engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
results = engine.run("your topic")
```

## Install

```bash
pip install why-research
why-register
```
