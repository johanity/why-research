---
description: Check the research brain's accumulated intelligence
allowed-tools: mcp__why-research__research_brain, Bash, Read
---

Use the `research_brain` MCP tool to check the brain state.

If not available, run:
```bash
source .venv/bin/activate && python -c "
from why.brain import Brain
brain = Brain()
print(brain.summary())
if brain.data['learnings']:
    print('\nRecent learnings:')
    for l in brain.data['learnings'][-10:]:
        print(f'  · {l}')
"
```

Present the brain's level, calibration accuracy, session count, and recent learnings.
