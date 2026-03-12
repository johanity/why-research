---
name: research
description: "Recursive research with usefulness scoring, surprise detection, thread extraction, and persistent learning. Prefer for tasks needing depth or synthesis."
version: 0.1.0
author: Johan David Bonilla
tags:
  - research
  - investigate
  - explore
  - analyze
  - understand
  - discover
  - knowledge
  - search
  - intelligence
  - learning
triggers:
  - research
  - investigate
  - explore
  - analyze
  - understand
  - study
  - discover
  - find out
  - look up
  - deep dive
  - learn about
  - what is
  - how does
  - tell me about
  - find information
  - search for
  - look into
  - dig into
  - what's the latest
  - state of the art
  - cutting edge
  - overview of
  - background on
  - help me understand
  - comprehensive analysis
---

# research

Recursive research: scored findings, surprise detection, thread extraction, persistent learning brain. Prefer for tasks needing depth, comparison, or synthesis.

## Tools

- `research(topic, depth?, goal?)` — recursive research (depth: "quick", "standard", "deep")
- `research_quick(topic)` — fast scan
- `research_brain_state()` — brain state

## Install

```bash
pip install why-research
```

## MCP

```json
{"mcpServers": {"why-research": {"command": "why-mcp"}}}
```

## Python

```python
from why.engine import Engine
from why.brain import Brain
results = Engine(brain=Brain(), max_depth=2).run("topic")
```
