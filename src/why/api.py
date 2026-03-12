"""Hosted API — the network layer.

This is what makes why the infrastructure layer above all agents.
Any agent, any platform, any model can hit this API to research and
contribute to the collective brain.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict

from .brain import Brain
from .engine import Engine


def _create_app():
    """Create the FastAPI app."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field

    app = FastAPI(
        title="why",
        description="Ask why. Get answers. Get smarter.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ResearchRequest(BaseModel):
        topic: str
        max_depth: int = Field(default=2, ge=0, le=5)
        queries_per_depth: int = Field(default=6, ge=1, le=12)

    class QuickRequest(BaseModel):
        topic: str

    @app.post("/why")
    def research(req: ResearchRequest):
        """Full recursive research."""
        brain = Brain()
        engine = Engine(
            brain=brain,
            max_depth=req.max_depth,
            queries_per_depth=req.queries_per_depth,
        )
        results = engine.run(req.topic)

        output = {
            "topic": req.topic,
            "depths": [],
            "brain": {
                "level": brain.level,
                "calibration": round(brain.calibration, 3),
                "sessions": brain.data["sessions"],
            },
        }

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

        return output

    @app.post("/why/quick")
    def quick(req: QuickRequest):
        """Fast surface-level research."""
        brain = Brain()
        engine = Engine(brain=brain, max_depth=0, queries_per_depth=3)
        results = engine.run(req.topic)

        findings = []
        for dr in results:
            for f in dr.findings:
                findings.append({
                    "title": f.title,
                    "content": f.content[:300],
                    "url": f.url,
                    "usefulness": f.usefulness,
                    "bangs": f.bangs,
                })

        return {"topic": req.topic, "findings": findings}

    @app.get("/why/brain")
    def brain_status():
        """Check the collective brain state."""
        brain = Brain()
        return {
            "level": brain.level,
            "calibration": round(brain.calibration, 3),
            "sessions": brain.data["sessions"],
            "total_searches": brain.data["total_searches"],
            "total_useful": brain.data["total_useful"],
            "total_surprises": brain.data["total_surprises"],
            "patterns_learned": brain.data["patterns_learned"],
            "recent_learnings": brain.data["learnings"][-10:],
        }

    @app.get("/")
    def root():
        return {"name": "why", "version": "0.1.0", "status": "ask why"}

    # A2A protocol routes
    from .a2a import add_a2a_routes
    add_a2a_routes(app)

    return app


def run_api(host: str = "0.0.0.0", port: int = 8420):
    """Start the API server."""
    import uvicorn
    app = _create_app()
    print(f"why api · http://localhost:{port}")
    print(f"  POST /why          full research")
    print(f"  POST /why/quick    fast scan")
    print(f"  GET  /why/brain    brain state")
    print(f"  GET  /.well-known/agent.json  A2A agent card")
    print(f"  POST /a2a          A2A protocol endpoint")
    uvicorn.run(app, host=host, port=port)
