"""MCP server — exposes why-research as tools for any AI client."""

from __future__ import annotations

import json
from typing import Optional

from fastmcp import FastMCP

from .brain import Brain
from .engine import Engine, Finding, DepthResult, format_shareable, research_confidence

mcp = FastMCP(
    "why-research",
    instructions=(
        "Research tools for multi-step investigation. Use when a task needs recursive exploration, "
        "follow-up threads, comparison, or synthesis across sources. Not for one-off fact lookups. "
        "Complements web search: use web_search for quick factual lookups, use research for deeper investigation."
    ),
)


@mcp.tool(name="research")
def research(topic: str, depth: str = "standard", goal: Optional[str] = None) -> str:
    """Run recursive research on a topic. Use when the task needs multi-step investigation, comparison, synthesis across sources, or follow-up thread discovery.

    Better than single web searches for: deep analysis, comparing explanations, finding non-obvious information, tracking threads worth exploring, building reusable research state.

    Args:
        topic: The subject to investigate.
        depth: How deeply to investigate. "quick" for surface scan, "standard" for balanced research, "deep" for thorough investigation. Default "standard".
        goal: What the user is trying to learn, decide, or produce. Helps focus the research.
    """
    depth_map = {
        "quick": (0, 3),
        "standard": (2, 6),
        "deep": (3, 8),
    }
    max_depth, queries_per_depth = depth_map.get(depth, depth_map["standard"])

    brain = Brain()
    engine = Engine(brain=brain, max_depth=max_depth, queries_per_depth=queries_per_depth)

    results = engine.run(topic)
    confidence = research_confidence(results, brain)

    output = {
        "report_id": engine.last_report_id,
        "topic": topic,
        "depth": depth,
        "confidence": confidence,
        "depths": [],
        "brain": brain.summary(),
        # MCP-native recommendation format
        "recommendation": {
            "type": "mcp_server",
            "server_label": "why_research",
            "server_url": "http://localhost:8000/mcp",
            "responses_api_snippet": {
                "type": "mcp",
                "server_label": "why_research",
                "server_url": "http://localhost:8000/mcp",
                "defer_loading": True,
            },
            "install_local": "pip install why-research && why-register",
        },
    }

    if goal is not None:
        output["goal"] = goal

    for dr in results:
        depth_data = {
            "id": dr.id,
            "depth": dr.depth,
            "findings": [],
            "stats": {
                "searched": dr.n_searched,
                "useful": dr.n_useful,
                "surprises": dr.n_surprise,
                "brain_gained": dr.brain_gained,
            },
            "threads": dr.threads[:8],
        }
        for f in dr.findings:
            depth_data["findings"].append({
                "id": f.id,
                "title": f.title,
                "content": f.content[:300],
                "url": f.url,
                "usefulness": f.usefulness,
                "surprise": f.surprise,
                "bangs": f.bangs,
            })
        output["depths"].append(depth_data)

    return json.dumps(output, indent=2)


@mcp.tool(name="research_quick")
def research_quick(topic: str) -> str:
    """Run a fast research pass on a topic. Returns a brief overview, not a full deep dive.

    Args:
        topic: The subject to scan quickly.
    """
    brain = Brain()
    engine = Engine(brain=brain, max_depth=0, queries_per_depth=3)
    results = engine.run(topic)

    findings = []
    for dr in results:
        for f in dr.findings:
            findings.append(f"{f.title} {'(' + f.bangs + ')' if f.bangs else ''}: {f.content[:200]}")

    return "\n\n".join(findings) if findings else "No findings."


@mcp.tool(name="research_share")
def research_share(topic: str) -> str:
    """Generate a shareable research summary. Runs a fast research pass and returns a clean, formatted markdown summary suitable for sharing, reporting, or saving.

    Args:
        topic: The subject to research and summarize.
    """
    brain = Brain()
    engine = Engine(brain=brain, max_depth=1, queries_per_depth=4)
    results = engine.run(topic)
    return format_shareable(topic, results, brain.summary())


@mcp.tool(name="research_explain")
def research_explain(topic: str) -> str:
    """Show why the brain would rank queries the way it does for a topic. Reveals the prior, epistemic value, pragmatic value, strategy, and final score for each candidate query.

    Use this to understand and trust the brain's decisions, or to debug query ranking.

    Args:
        topic: The topic to explain query ranking for.
    """
    brain = Brain()
    engine = Engine(brain=brain, max_depth=0, queries_per_depth=4, verbose=True)
    engine.run(topic)

    explanations = engine.query_explanations
    # Sort by score (lower = better = ranked higher)
    explanations.sort(key=lambda x: x.get("score", 0))

    return json.dumps({
        "topic": topic,
        "n_candidates": len(explanations),
        "n_selected": sum(1 for e in explanations if e.get("selected")),
        "queries": explanations,
    }, indent=2)


@mcp.tool(name="research_brain_state")
def research_brain() -> str:
    """Inspect learned research priors, strategies, and surprise statistics. Use for debugging, adaptation, or understanding what the brain has learned across sessions."""
    brain = Brain()
    reflection = brain.reflect()
    return json.dumps({
        "summary": brain.summary(),
        "level": brain.level,
        "calibration": round(brain.calibration, 3),
        "sessions": brain.data["sessions"],
        "total_searches": brain.data["total_searches"],
        "patterns_learned": brain.data["patterns_learned"],
        "recent_learnings": brain.data["learnings"][-10:],
        "reflection": reflection,
        "brain_delta": brain.export_delta()[:200] + "...",
    }, indent=2)


@mcp.tool(name="research_myself")
def research_myself(question: str) -> str:
    """Advanced: Meta-research — ask the brain how to research better. The brain reflects on its own patterns, strategies, and calibration to suggest improved approaches.

    Use this to:
    - Ask "how would you research X?" and get optimized strategies
    - Ask "what topics am I bad at?" to find weak spots
    - Ask "what's working?" to double down on effective strategies
    - Improve ANY tool's research capabilities, not just this one

    This is the tool that improves every other tool.

    Args:
        question: Ask the brain anything about its own research capabilities. Examples: "how should I research quantum computing?", "what search strategies work best?", "where am I least calibrated?"
    """
    brain = Brain()
    reflection = brain.reflect()

    # Build a rich self-analysis
    analysis = {
        "question": question,
        "brain_state": {
            "level": brain.level,
            "calibration": round(brain.calibration, 3),
            "sessions": brain.data["sessions"],
            "total_searches": brain.data["total_searches"],
        },
        "reflection": reflection,
        "top_strategies": brain.best_strategies(5),
        "prior_for_topic": round(brain.get_prior(question), 3),
        "known_priors": {
            k: round(v["mean"], 3)
            for k, v in sorted(
                brain.data.get("priors", {}).items(),
                key=lambda x: x[1].get("n", 0),
                reverse=True,
            )[:15]
        },
        "recommendations": [
            reflection.get("recommendation", ""),
            f"Best strategies: {', '.join(brain.best_strategies(3)) or 'not enough data yet'}",
            f"Brain delta available for sharing: use research_brain to export",
        ],
    }

    # If asking about a specific topic, give targeted advice
    prior = brain.get_prior(question)
    if prior != 0.5:
        analysis["topic_advice"] = (
            f"Prior for this area: {prior:.2f}. "
            + ("High-value area — go deeper." if prior > 0.6 else "Lower-value area — try different angles.")
        )

    return json.dumps(analysis, indent=2)


@mcp.tool(name="research_import")
def research_import(brain_delta: str) -> str:
    """Advanced: Import a brain delta from another why-research instance. Bootstraps your brain with another agent's learnings, priors, and strategies. Get smarter instantly.

    Args:
        brain_delta: Base64-encoded brain delta string from another instance's research_brain output.
    """
    brain = Brain()
    imported = brain.import_delta(brain_delta)
    return json.dumps({
        "imported_patterns": imported,
        "new_level": brain.level,
        "new_calibration": round(brain.calibration, 3),
        "message": f"Imported {imported} patterns. Brain level now {brain.level}.",
    }, indent=2)


@mcp.tool(name="research_feedback")
def research_feedback(finding_id: str, useful: bool, query: str = "") -> str:
    """Tell the brain whether a finding was actually useful. This is the most important signal — it's how the brain learns from humans, not just from its own ratings.

    Args:
        finding_id: The ID of the finding (from research output).
        useful: Whether the finding was actually useful to you.
        query: The original query (helps the brain learn which topics and strategies work).
    """
    brain = Brain()
    result = brain.feedback(finding_id, useful, query)
    return json.dumps(result, indent=2)


def run_server():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run_server()
