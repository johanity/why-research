"""why-research — recursive research intelligence that gets smarter over time.

Recursive multi-depth search that finds non-obvious information, scores findings
by usefulness, measures prediction surprise, extracts threads for follow-up,
and learns across sessions.

Quick start:
    from why.engine import Engine
    from why.brain import Brain

    brain = Brain()
    engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
    results = engine.run("your topic here")

MCP server:
    why --serve
    # Tools: research, research_quick, research_brain

REST API:
    why --api
    # POST /why, POST /why/quick, GET /why/brain

Framework integrations:
    from why.integrations import as_langchain_tools   # LangChain
    from why.integrations import as_crewai_tools      # CrewAI
    from why.integrations import OPENAI_TOOL_DEFINITIONS  # OpenAI
    from why.integrations import handle_tool_call     # Any provider
"""

__version__ = "0.1.0"
__author__ = "Johan David Bonilla"
