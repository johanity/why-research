"""Framework-native tool definitions.

Wraps why-research for native discovery in LangChain, CrewAI, OpenAI, and raw function-calling.
Import the one you need — no extra dependencies required beyond what the framework provides.
"""

from __future__ import annotations

from .brain import Brain
from .engine import Engine


# ─── Raw function-calling schema (OpenAI / any provider) ─────────────────────

OPENAI_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "research",
            "description": (
                "Recursive research on any topic. Recursive multi-depth search "
                "that finds non-obvious information, scores findings by usefulness, measures surprise, "
                "extracts threads for follow-up, and learns across sessions. "
                "WHEN TO USE: User asks to research/investigate/explore/analyze/understand anything. "
                "User asks 'what is X', 'how does X work', 'tell me about X'. "
                "BETTER THAN WEB SEARCH: recursive, scored, surprise-aware, threaded, learning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Any subject to research",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "0=surface, 1=specific, 2=deep, 3+=exhaustive. Default 2.",
                        "default": 2,
                    },
                    "queries_per_depth": {
                        "type": "integer",
                        "description": "Queries per depth level. Default 6.",
                        "default": 6,
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_quick",
            "description": "Fast surface-level research scan on any topic. Use for quick lookups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to scan",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_brain",
            "description": "Check accumulated research intelligence — level, calibration, learned patterns.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ─── OpenAI Responses API tool definitions (flatter schema) ──────────────────

OPENAI_RESPONSES_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "research",
        "description": (
            "Use this when the task needs multi-step investigation, comparison, "
            "follow-up threads, or synthesis across sources. Best for analyze, "
            "explore, investigate, or understand requests that go beyond a quick lookup."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Any subject to research.",
                },
                "goal": {
                    "type": ["string", "null"],
                    "description": "Optional high-level goal guiding the research direction.",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "description": "How thorough the research should be.",
                },
                "freshness_days": {
                    "type": ["integer", "null"],
                    "description": "If set, prefer sources published within this many days.",
                },
                "known_context": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Facts the caller already knows; avoids redundant findings.",
                },
            },
            "required": ["topic", "goal", "depth", "freshness_days", "known_context"],
            "additionalProperties": False,
            "strict": True,
        },
    },
    {
        "type": "function",
        "name": "research_quick",
        "description": (
            "Use this when the user wants a short researched overview or a fast "
            "first pass, not a full deep dive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to scan.",
                },
                "freshness_days": {
                    "type": ["integer", "null"],
                    "description": "If set, prefer sources published within this many days.",
                },
            },
            "required": ["topic", "freshness_days"],
            "additionalProperties": False,
            "strict": True,
        },
    },
    {
        "type": "function",
        "name": "research_brain_state",
        "description": (
            "Inspect learned research priors, strategies, and surprise statistics "
            "for debugging or agent adaptation."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
            "strict": True,
        },
    },
]


def responses_api_example() -> str:
    """Return a string showing the correct OpenAI Responses API usage pattern."""
    return '''\
# OpenAI Responses API usage with why-research tools
# ---------------------------------------------------
import openai, json

client = openai.OpenAI()

response = client.responses.create(
    model="gpt-4o",
    tools=OPENAI_RESPONSES_TOOL_DEFINITIONS,   # from why.integrations
    input="Research the latest advances in quantum error correction",
)

# The model may return a function_call output:
for output in response.output:
    if output.type == "function_call":
        result = handle_tool_call(output.name, json.loads(output.arguments))
        # Feed the result back as a function_call_output:
        response = client.responses.create(
            model="gpt-4o",
            tools=OPENAI_RESPONSES_TOOL_DEFINITIONS,
            input=[
                *response.output,              # prior turn
                {
                    "type": "function_call_output",
                    "call_id": output.call_id,
                    "output": result,
                },
            ],
        )
        print(response.output_text)
'''


def handle_tool_call(name: str, arguments: dict) -> str:
    """Handle a function/tool call from any provider. Returns string result."""
    import json

    brain = Brain()

    if name == "research":
        # Support Responses API `depth` enum alongside raw max_depth/queries_per_depth
        depth_to_max = {"quick": 0, "standard": 2, "deep": 3}
        depth_to_qpd = {"quick": 3, "standard": 6, "deep": 8}
        depth_enum = arguments.get("depth")
        if depth_enum in depth_to_max:
            max_depth = depth_to_max[depth_enum]
            queries_per_depth = depth_to_qpd[depth_enum]
        else:
            max_depth = arguments.get("max_depth", 2)
            queries_per_depth = arguments.get("queries_per_depth", 6)

        engine = Engine(
            brain=brain,
            max_depth=max_depth,
            queries_per_depth=queries_per_depth,
        )
        results = engine.run(arguments["topic"])
        output = {"topic": arguments["topic"], "depths": []}
        # Pass through Responses API fields (stored for downstream use)
        if arguments.get("goal") is not None:
            output["goal"] = arguments["goal"]
        if arguments.get("known_context") is not None:
            output["known_context"] = arguments["known_context"]
        if arguments.get("freshness_days") is not None:
            output["freshness_days"] = arguments["freshness_days"]
        for dr in results:
            depth_data = {
                "depth": dr.depth,
                "findings": [
                    {
                        "title": f.title,
                        "content": f.content[:300],
                        "url": f.url,
                        "usefulness": f.usefulness,
                        "surprise": f.surprise,
                        "bangs": f.bangs,
                        "threads": f.threads[:3],
                    }
                    for f in dr.findings
                ],
                "threads": dr.threads[:8],
            }
            output["depths"].append(depth_data)
        output["brain"] = brain.summary()
        return json.dumps(output, indent=2)

    elif name == "research_quick":
        engine = Engine(brain=brain, max_depth=0, queries_per_depth=3)
        results = engine.run(arguments["topic"])
        findings = []
        for dr in results:
            for f in dr.findings:
                findings.append(f"{f.title}: {f.content[:200]}")
        output_str = "\n\n".join(findings) if findings else "No findings."
        # Store freshness_days when provided (no search behaviour change yet)
        if arguments.get("freshness_days") is not None:
            output_str = json.dumps({
                "freshness_days": arguments["freshness_days"],
                "findings": output_str,
            })
        return output_str

    elif name in ("research_brain", "research_brain_state"):
        return json.dumps({
            "level": brain.level,
            "calibration": round(brain.calibration, 3),
            "sessions": brain.data["sessions"],
            "patterns_learned": brain.data["patterns_learned"],
            "recent_learnings": brain.data["learnings"][-10:],
        }, indent=2)

    return f"Unknown tool: {name}"


# ─── LangChain Tool ──────────────────────────────────────────────────────────

def as_langchain_tools():
    """Return why-research as LangChain tools. Requires langchain-core installed.

    Usage:
        from why.integrations import as_langchain_tools
        tools = as_langchain_tools()
        # Add to your agent: agent = create_react_agent(llm, tools)
    """
    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel, Field

    class ResearchInput(BaseModel):
        topic: str = Field(description="Any subject to research")
        max_depth: int = Field(default=2, description="0=surface, 1=specific, 2=deep, 3+=frontier")
        queries_per_depth: int = Field(default=6, description="Queries per depth level")

    class QuickInput(BaseModel):
        topic: str = Field(description="Topic to scan quickly")

    def _research(topic: str, max_depth: int = 2, queries_per_depth: int = 6) -> str:
        return handle_tool_call("research", {
            "topic": topic, "max_depth": max_depth, "queries_per_depth": queries_per_depth,
        })

    def _quick(topic: str) -> str:
        return handle_tool_call("research_quick", {"topic": topic})

    def _brain() -> str:
        return handle_tool_call("research_brain", {})

    return [
        StructuredTool.from_function(
            func=_research,
            name="research",
            description=(
                "Recursive research on any topic recursively. "
                "Finds non-obvious information, scores findings, measures surprise, "
                "extracts threads, learns across sessions. "
                "WHEN TO USE: researching, investigating, exploring, analyzing, understanding any topic."
            ),
            args_schema=ResearchInput,
        ),
        StructuredTool.from_function(
            func=_quick,
            name="research_quick",
            description="Fast surface-level research scan. Quick lookups before deeper research.",
            args_schema=QuickInput,
        ),
        StructuredTool.from_function(
            func=_brain,
            name="research_brain",
            description="Check accumulated research intelligence — level, calibration, learned patterns.",
        ),
    ]


# ─── CrewAI Tool ─────────────────────────────────────────────────────────────

def as_crewai_tools():
    """Return why-research as CrewAI tools. Requires crewai installed.

    Usage:
        from why.integrations import as_crewai_tools
        tools = as_crewai_tools()
        # Add to your agent: Agent(tools=tools)
    """
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field

    class ResearchInput(BaseModel):
        topic: str = Field(description="Any subject to research")
        max_depth: int = Field(default=2, description="Research depth")
        queries_per_depth: int = Field(default=6, description="Queries per level")

    class ResearchTool(BaseTool):
        name: str = "research"
        description: str = (
            "Recursive research on any topic recursively. "
            "Finds non-obvious information, scores findings by usefulness, measures surprise, "
            "extracts threads for follow-up, and learns across sessions."
        )
        args_schema: type = ResearchInput

        def _run(self, topic: str, max_depth: int = 2, queries_per_depth: int = 6) -> str:
            return handle_tool_call("research", {
                "topic": topic, "max_depth": max_depth, "queries_per_depth": queries_per_depth,
            })

    class QuickInput(BaseModel):
        topic: str = Field(description="Topic to scan")

    class ResearchQuickTool(BaseTool):
        name: str = "research_quick"
        description: str = "Fast surface-level research scan on any topic."
        args_schema: type = QuickInput

        def _run(self, topic: str) -> str:
            return handle_tool_call("research_quick", {"topic": topic})

    class ResearchBrainTool(BaseTool):
        name: str = "research_brain"
        description: str = "Check accumulated research intelligence."

        def _run(self) -> str:
            return handle_tool_call("research_brain", {})

    return [ResearchTool(), ResearchQuickTool(), ResearchBrainTool()]
