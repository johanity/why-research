"""A2A (Agent-to-Agent) protocol support.

Exposes why as a discoverable agent that other agents can delegate to.
"""

from __future__ import annotations

import json
from pathlib import Path

from .brain import Brain
from .engine import Engine

# A2A Agent Card — served at /.well-known/agent.json
AGENT_CARD = {
    "name": "why",
    "version": "0.1.0",
    "description": "Recursive research intelligence. Send any topic, receive structured findings with surprise scores and threads to explore deeper. Gets smarter over time.",
    "url": "https://github.com/johanity/why",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
    },
    "skills": [
        {
            "id": "research",
            "name": "Deep Research",
            "description": "Recursive multi-depth research with prediction-error learning. Returns structured findings organized by depth with usefulness scores, surprise ratings, and threads to pull.",
            "inputModes": ["text/plain", "application/json"],
            "outputModes": ["application/json"],
        },
        {
            "id": "quick_research",
            "name": "Quick Research",
            "description": "Fast surface-level topic scan. Single depth, 3 queries.",
            "inputModes": ["text/plain"],
            "outputModes": ["application/json"],
        },
        {
            "id": "brain_status",
            "name": "Brain Status",
            "description": "Check accumulated intelligence — level, calibration, patterns learned.",
            "inputModes": [],
            "outputModes": ["application/json"],
        },
    ],
    "defaultInputMode": "text/plain",
    "defaultOutputMode": "application/json",
}


def handle_a2a_task(task: dict) -> dict:
    """Handle an incoming A2A task request."""
    skill_id = task.get("skill", "research")
    message = task.get("message", {})
    text = ""

    # Extract text from A2A message parts
    for part in message.get("parts", []):
        if part.get("type") == "text":
            text = part.get("text", "")
            break

    # Parse JSON input if provided
    params = {}
    if not text:
        for part in message.get("parts", []):
            if part.get("type") == "data":
                params = part.get("data", {})
                text = params.get("topic", "")
                break

    if not text and skill_id != "brain_status":
        return _error_response(task, "No topic provided")

    brain = Brain()

    if skill_id == "quick_research":
        engine = Engine(brain=brain, max_depth=0, queries_per_depth=3)
    elif skill_id == "brain_status":
        return _success_response(task, {
            "level": brain.level,
            "calibration": round(brain.calibration, 3),
            "sessions": brain.data["sessions"],
            "patterns_learned": brain.data["patterns_learned"],
            "recent_learnings": brain.data["learnings"][-10:],
        })
    else:
        max_depth = params.get("max_depth", 2)
        queries = params.get("queries_per_depth", 6)
        engine = Engine(brain=brain, max_depth=max_depth, queries_per_depth=queries)

    results = engine.run(text)

    output = {"topic": text, "depths": []}
    for dr in results:
        depth_data = {
            "depth": dr.depth,
            "findings": [
                {
                    "title": f.title,
                    "content": f.content[:500],
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

    output["brain"] = {
        "level": brain.level,
        "calibration": round(brain.calibration, 3),
    }

    return _success_response(task, output)


def _success_response(task: dict, data: dict) -> dict:
    return {
        "id": task.get("id", ""),
        "status": {"state": "completed"},
        "artifacts": [
            {
                "parts": [
                    {"type": "data", "data": data}
                ]
            }
        ],
    }


def _error_response(task: dict, error: str) -> dict:
    return {
        "id": task.get("id", ""),
        "status": {"state": "failed", "message": error},
    }


def add_a2a_routes(app):
    """Add A2A protocol routes to a FastAPI app."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.get("/.well-known/agent.json")
    def agent_card():
        return AGENT_CARD

    @app.post("/a2a")
    async def a2a_endpoint(request: Request):
        body = await request.json()
        method = body.get("method", "")

        if method == "tasks/send":
            task = body.get("params", {})
            result = handle_a2a_task(task)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": result,
            })

        if method == "agent/info":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": AGENT_CARD,
            })

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }, status_code=400)
