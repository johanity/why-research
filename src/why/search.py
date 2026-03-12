"""Search layer — finds real information from the web.

Uses Tavily for web search (built for AI agents, returns clean content).
Falls back to LLM knowledge if no API key is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0


def search(query: str, max_results: int = 5) -> List[SearchResult]:
    """Search the web. Uses Tavily if available, else LLM fallback."""
    api_key = os.environ.get("TAVILY_API_KEY")

    if api_key:
        return _tavily_search(query, max_results, api_key)
    return _llm_search(query, max_results)


def _tavily_search(query: str, max_results: int, api_key: str) -> List[SearchResult]:
    """Real web search via Tavily."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=False,
        )

        results = []
        for r in response.get("results", []):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
            ))
        return results
    except Exception as e:
        return _llm_search(query, max_results)


def _llm_search(query: str, max_results: int) -> List[SearchResult]:
    """Fallback: use LLM's own knowledge."""
    import litellm
    import json

    response = litellm.completion(
        model=os.environ.get("WHY_MODEL", "claude-sonnet-4-20250514"),
        messages=[
            {"role": "system", "content": (
                "You are a research engine. Return the most specific, technical, "
                "non-obvious information about the query. Include real names, "
                "numbers, dates, and sources where possible."
            )},
            {"role": "user", "content": (
                f"Research: {query}\n\n"
                f"Return JSON array of {max_results} findings:\n"
                '[{"title": "...", "content": "detailed finding...", "url": "source if known"}]'
            )},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    text = response.choices[0].message.content.strip()

    try:
        # Parse JSON from response
        if "```" in text:
            for block in text.split("```")[1::2]:
                clean = block.strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
                try:
                    items = json.loads(clean)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                items = json.loads(text)
        else:
            items = json.loads(text)

        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=0.5,
            )
            for item in items[:max_results]
        ]
    except (json.JSONDecodeError, Exception):
        return [SearchResult(title="raw", url="", content=text, score=0.5)]
