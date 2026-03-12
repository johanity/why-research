# why

Research that learns. Every session makes the next one smarter.

```
pip install why-research
```

## What happens when you use it

1. You ask a question
2. It searches recursively at multiple depths
3. It **predicts** how useful each result will be — then checks how wrong it was
4. The prediction error is the learning signal
5. Next time, it's better

```
$ why "swarm intelligence"

              ·
         ·  emergent coordination           !!
        ··  stigmergy mechanisms             !!!
       ···  ant colony optimization          !
      ····  boid flocking rules              !!
       ···  decentralized consensus          !!!
        ··  swarm robotics 2026              !!!!
         ·  collective decision-making       !!
              ·

     14·9✦·4!·+7🧠

     swarm_intelligence.md

     6 threads left to pull ↓
```

The brain persists at `~/.why/brain.json`. Priors, strategies, calibration — all accumulate across sessions.

## Why not just use ChatGPT / Perplexity / etc?

They forget everything between conversations. You get the same quality whether it's your 1st query or your 1000th.

`why` gets measurably better:
- **Session 1**: Calibration 0%, no priors, no strategy data
- **Session 50**: Calibration 85%+, topic priors across domains, refined strategies
- **Session 500**: Brain deltas exportable to bootstrap new instances instantly

The difference compounds. A tool that learns your research patterns outperforms a stateless genius on the tasks you actually care about.

## The research behind it

This isn't a wrapper. The prediction-error learning loop is backed by published experiments:

1. [**barcaui-predicted-karpathy**](https://github.com/johanity/barcaui-predicted-karpathy) — Showed that AI agents plateau when they search without predicting. The same cognitive shortcut that makes students worse at learning makes AI agents worse at research.

2. [**theorist**](https://github.com/johanity/theorist) — Extracted the principle into a general-purpose library. Prediction-error optimization. One file, zero dependencies.

3. [**epistemic-autoresearch**](https://github.com/johanity/epistemic-autoresearch) — 251 experiments. The predicting agent adapted to a 5x compute shift on try one. The searching agent never caught up.

`why` is the productized version of these findings.

## 9 ways to use it

### 1. CLI
```bash
why "topic"             # one-shot research
why                     # interactive REPL
why --brain             # brain state
```

Interactive commands: `deep <topic>`, `quick <topic>`, `threads`, `brain`, `<number>` to follow a thread.

### 2. MCP Server (Claude, Cursor, Copilot, Codex, Gemini, any MCP client)
```bash
why --serve
```
```json
{"mcpServers": {"why-research": {"command": "why-mcp"}}}
```
Tools: `research`, `research_quick`, `research_share`, `research_brain_state`, `research_myself`, `research_import`

### 3. REST API
```bash
why --api  # localhost:8420
```
```
POST /why          {"topic": "swarms", "depth": "standard"}
POST /why/quick    {"topic": "redis"}
GET  /why/brain
```

### 4. A2A Protocol (agent-to-agent)
```
GET  /.well-known/agent.json
POST /a2a  (JSON-RPC 2.0)
```

### 5. Python
```python
from why.engine import Engine
from why.brain import Brain

brain = Brain()
results = Engine(brain=brain, max_depth=2).run("your topic")
# results: List[DepthResult], each with List[Finding]
# Finding: title, content, url, usefulness, surprise, bangs, threads
```

### 6. LangChain
```python
from why.integrations import as_langchain_tools
tools = as_langchain_tools()
```

### 7. CrewAI
```python
from why.integrations import as_crewai_tools
tools = as_crewai_tools()
```

### 8. OpenAI function calling
```python
from why.integrations import OPENAI_TOOL_DEFINITIONS, handle_tool_call
```

### 9. Docker
```bash
docker build -t why .
docker run -e ANTHROPIC_API_KEY=sk-ant-... why "swarms"
```

## Auto-registration

```bash
why-register
```

Adds `why-research` to Claude Code's MCP servers, installs the research skill globally, and appends routing guidance to your global CLAUDE.md.

## How the brain works

| Step | What happens |
|------|-------------|
| 1 | Generate search queries + **predict** usefulness (0.0–1.0) |
| 2 | Execute searches (Tavily web search or LLM knowledge) |
| 3 | Extract findings + rate **actual** usefulness |
| 4 | Compute **surprise** = \|predicted − actual\| |
| 5 | Update priors, strategies, calibration |
| 6 | Recurse deeper on extracted threads |
| 7 | Track strategy effectiveness across sessions |

Brain data is portable — export with `research_brain_state()`, import with `research_import(delta)`.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | LLM calls via litellm |
| `TAVILY_API_KEY` | No | Real web search ([tavily.com](https://tavily.com)) |
| `WHY_MODEL` | No | Override model (default: claude-sonnet-4-20250514) |

## License

MIT — Johan David Bonilla / Mindful AGI Systems
