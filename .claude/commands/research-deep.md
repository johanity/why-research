---
description: Deep recursive research (3 levels, 8 queries per level)
allowed-tools: mcp__why-research__research, Bash, Read, Write
---

Use the `research` MCP tool with max_depth=3 and queries_per_depth=8 to do a deep recursive research on: $ARGUMENTS

If the MCP tool is not available, run via CLI:
```bash
source .venv/bin/activate && python -c "
from why.engine import Engine
from why.brain import Brain
import json

brain = Brain()
engine = Engine(brain=brain, max_depth=3, queries_per_depth=8)
results = engine.run('$ARGUMENTS')

for dr in results:
    print(f'\n## Depth {dr.depth}')
    for f in dr.findings:
        bangs = f' {f.bangs}' if f.bangs else ''
        print(f'  {f.title}{bangs} (useful: {f.usefulness:.1f}, surprise: {f.surprise:.1f})')
        if f.content:
            print(f'    {f.content[:200]}')
        if f.threads:
            print(f'    threads: {f.threads}')
"
```

Present findings organized by depth level. Emphasize high-surprise discoveries.
