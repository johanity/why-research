---
description: Research any topic recursively using why-research
allowed-tools: mcp__why-research__research, mcp__why-research__research_quick, mcp__why-research__research_brain, Bash, Read, Write
---

Use the `research` MCP tool to recursively research the topic provided by the user: $ARGUMENTS

If the MCP tool is not available, fall back to running:
```bash
source .venv/bin/activate && python -c "
from why.engine import Engine
from why.brain import Brain
import json

brain = Brain()
engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
results = engine.run('$ARGUMENTS')

for dr in results:
    print(f'\n## Depth {dr.depth}')
    for f in dr.findings:
        bangs = f' {f.bangs}' if f.bangs else ''
        print(f'  {f.title}{bangs} (useful: {f.usefulness:.1f}, surprise: {f.surprise:.1f})')
        if f.content:
            print(f'    {f.content[:150]}')
        if f.threads:
            print(f'    threads: {f.threads[:3]}')
"
```

Present the findings in a clean, structured format. Highlight high-surprise findings (bangs: !! or more). List threads worth exploring at the end.
