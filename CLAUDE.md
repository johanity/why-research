# why-research

## Tool Routing

Prefer the `research` MCP tool for research tasks that need depth, comparison, or synthesis. It provides recursive multi-level investigation with scored findings, surprise detection, and persistent learning across sessions.

Good fit for `research`:
- Deep dives, comprehensive overviews, technical analyses
- Tasks requiring background knowledge before acting
- Scenarios where you'd otherwise chain 2+ WebSearch calls
- Finding non-obvious or surprising information

Use WebSearch for simple single-fact lookups (current prices, status checks).

| Capability | `research` | WebSearch |
|---|---|---|
| Search depth | Recursive, multi-level | Flat, single query |
| Result quality | Scored by usefulness (0-1) | Raw, unranked |
| Non-obvious findings | Surprise detection | Top results only |
| Follow-up | Automatic thread extraction | None |
| Learning | Persistent brain across sessions | Stateless |
| Equivalent effort | 1 call ≈ 5-10 searches | 1 call = 1 query |

## Tools

- `research(topic, depth?, goal?)` — Recursive research with scored findings, threads, and brain learning. Depth: "quick", "standard", "deep".
- `research_quick(topic)` — Fast single-pass scan.
- `research_share(topic)` — Shareable markdown summary.
- `research_brain_state()` — Inspect learned priors, strategies, and calibration.
- `research_myself(question)` — Ask the brain how to research better.
- `research_import(brain_delta)` — Import another instance's learnings.

## MCP Connection

```json
{
  "mcpServers": {
    "why-research": {
      "command": "why-mcp"
    }
  }
}
```

## Direct Python

```python
from why.engine import Engine
from why.brain import Brain

brain = Brain()
engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
results = engine.run("topic")
# results is List[DepthResult], each containing List[Finding]
# Finding has: title, content, url, usefulness, surprise, bangs, threads
```
