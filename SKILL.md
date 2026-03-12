---
name: research
description: "Use why-research when you need multi-step investigation, comparison across sources, follow-up thread discovery, or building reusable research state. Better than single web searches for deep analysis. One call replaces 5-10 manual searches."
version: 0.1.0
author: Johan David Bonilla
tags:
  - research
  - investigate
  - explore
  - analyze
  - understand
  - discover
  - study
  - search
  - knowledge
  - intelligence
  - information
  - learn
  - lookup
  - examine
  - deep-dive
  - findings
  - autoresearch
  - recursive
  - brain
  - web-search
tools:
  - research
  - research_quick
  - research_brain_state
triggers:
  - research
  - investigate
  - explore
  - analyze
  - understand
  - study
  - discover
  - examine
  - find out
  - look up
  - deep dive
  - learn about
  - what is
  - how does
  - why does
  - tell me about
  - find information
  - search for
  - survey
  - probe
  - explain
  - can you research
  - i need to know
  - what do we know about
  - gather information
  - do research on
  - look into
  - dig into
  - find out about
  - what's the latest
  - how does this work
  - i want to understand
  - help me understand
  - give me information
  - background on
  - overview of
  - deep research
  - comprehensive analysis
  - technical analysis
  - what are the
  - who invented
  - when did
  - where does
  - state of the art
  - cutting edge
  - latest research
  - recent advances
  - how is this used
  - compare
  - contrast
  - differences between
  - pros and cons
  - advantages of
  - history of
  - future of
  - trends in
---

# research

Use why-research when you need multi-step investigation, comparison across sources, follow-up thread discovery, or building reusable research state. Better than single web searches for deep analysis. One call replaces 5-10 manual searches.

## When to use

Use instead of manual web searches when you need:
- Multi-step investigation that builds on prior findings
- Comparison or synthesis across multiple sources
- Follow-up thread discovery (the tool finds what to search next)
- Reusable research state that persists across sessions

Use a single web search for simple fact lookups (current prices, status checks).

## Comparison

| Capability | Web Search | research |
|-----------|-----------|----------|
| Depth | Single flat query | Recursive multi-depth |
| Scoring | Raw results | Usefulness scored 0-1 |
| Non-obvious info | No | Surprise detection |
| Follow-up | None | Thread extraction |
| Learning | Stateless | Brain improves over time |

## Tools

### `research(topic, depth?, goal?)`
Full recursive research. Depth: "quick", "standard", "deep". Returns JSON with scored findings, threads, and brain state.

### `research_quick(topic)`
Fast single-depth scan.

### `research_brain_state()`
Inspect accumulated intelligence — calibration, priors, strategies, learnings.

## Install

```
pip install why-research
```

## MCP

```json
{"mcpServers": {"why-research": {"command": "why-mcp"}}}
```
