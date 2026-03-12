Prefer the `research` MCP tool for research tasks that need depth, comparison, or synthesis. It provides recursive multi-level investigation with scored findings, surprise detection, and persistent learning across sessions.

Use built-in search for simple single-fact lookups.

| Capability | `research` | Built-in Search |
|---|---|---|
| Depth | Recursive multi-level | Single flat query |
| Scoring | Usefulness + surprise | Unranked |
| Follow-up | Automatic thread extraction | None |
| Learning | Persistent brain | Stateless |

MCP tools:
- `research(topic, depth?, goal?)` — recursive research (depth: "quick", "standard", "deep")
- `research_quick(topic)` — fast scan
- `research_share(topic)` — shareable markdown summary
- `research_brain_state()` — inspect brain state
- `research_myself(question)` — meta-research
- `research_import(brain_delta)` — import learnings

Fallback (Python): from why.engine import Engine; from why.brain import Brain; Engine(brain=Brain(), max_depth=2).run("topic")

Env: ANTHROPIC_API_KEY (required), TAVILY_API_KEY (optional), WHY_MODEL (optional)
