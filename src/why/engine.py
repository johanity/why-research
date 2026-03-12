"""The recursive research engine — the core loop of why.

For each depth level:
1. Generate search queries + predict usefulness
2. Execute searches
3. Extract findings + rate actual usefulness
4. Measure surprise (predicted vs actual)
5. Extract threads to pull deeper
6. Recurse

The brain learns across sessions which search strategies work.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import litellm

from .brain import Brain
from .search import SearchResult, search


@dataclass
class Finding:
    """One research finding."""
    title: str
    content: str
    url: str
    usefulness: float  # 0-1 actual
    predicted: float  # 0-1 predicted
    surprise: float
    bangs: str  # "", "!", "!!", "!!!", "!!!!"
    id: str = ""  # stable finding ID
    depth: int = 0
    threads: List[str] = field(default_factory=list)  # sub-topics to recurse


@dataclass
class DepthResult:
    """Results from one depth level."""
    depth: int
    findings: List[Finding]
    n_searched: int
    n_useful: int
    id: str = ""  # stable depth result ID
    n_surprise: int = 0
    brain_gained: int = 0
    threads: List[str] = field(default_factory=list)


def usefulness_to_bangs(usefulness: float, surprise: float) -> str:
    """Convert usefulness + surprise into bang rating."""
    combined = usefulness * 0.6 + surprise * 0.4
    if combined >= 0.9:
        return "!!!!"
    if combined >= 0.75:
        return "!!!"
    if combined >= 0.6:
        return "!!"
    if combined >= 0.45:
        return "!"
    return ""


QUERY_PROMPT = """Generate {n} search queries to research: "{topic}"

Depth level: {depth} (0=broad, 1=specific, 2+=deep nuances)

{context}

Return the most specific, non-obvious queries that will find cutting-edge
technical information. Avoid generic queries.

For each query, predict how useful the results will be (0.0-1.0).

JSON only:
{{"queries": [{{"q": "query text", "p": 0.7}}]}}"""


EXTRACT_PROMPT = """Extract findings from these search results for the topic: "{topic}"

Results:
{results}

For each result, rate usefulness (0.0-1.0) and extract 1-2 threads worth
researching deeper.

JSON only:
{{"findings": [{{"title": "short title (max 30 chars)", "usefulness": 0.8, "threads": ["sub-topic 1"]}}]}}"""


class Engine:
    """The recursive research engine."""

    def __init__(
        self,
        brain: Brain,
        model: str = "claude-sonnet-4-20250514",
        max_depth: int = 2,
        queries_per_depth: int = 6,
        verbose: bool = False,
    ) -> None:
        self.brain = brain
        self.model = os.environ.get("WHY_MODEL", model)
        self.max_depth = max_depth
        self.queries_per_depth = queries_per_depth
        self.verbose = verbose
        self.query_explanations: List[Dict[str, Any]] = []

    def run(self, topic: str, on_finding=None, on_depth_start=None, on_depth_end=None) -> List[DepthResult]:
        """Run the full recursive research loop. Callbacks for live rendering."""
        self.query_explanations = []
        self.brain.start_session()
        all_results: List[DepthResult] = []
        all_threads: List[str] = [topic]

        for depth in range(self.max_depth + 1):
            if not all_threads:
                break

            # Pick threads to explore at this depth
            threads_this_level = all_threads[:max(2, self.queries_per_depth - depth * 2)]
            all_threads = []

            if on_depth_start:
                on_depth_start(depth)

            depth_result = self._research_depth(
                threads_this_level, depth, on_finding
            )
            all_results.append(depth_result)

            # Collect threads for next depth
            all_threads = depth_result.threads[:self.queries_per_depth]

            if on_depth_end:
                on_depth_end(depth, depth_result)

        # Generate stable IDs for multi-turn follow-up
        report_id = hashlib.md5(f"{topic}:{time.time()}".encode()).hexdigest()[:12]
        self.last_report_id = report_id
        for dr in all_results:
            dr.id = f"{report_id}-d{dr.depth}"
            for index, f in enumerate(dr.findings):
                f.id = f"{report_id}-d{dr.depth}-f{index}"

        self.brain.save()
        return all_results

    def _research_depth(
        self,
        topics: List[str],
        depth: int,
        on_finding=None,
    ) -> DepthResult:
        """Research one depth level."""
        # Generate queries with predictions
        queries = self._generate_queries(topics, depth)

        findings: List[Finding] = []
        all_threads: List[str] = []
        n_useful = 0
        n_surprise = 0
        brain_gained = 0

        for q_text, predicted in queries:
            # Search
            results = search(q_text, max_results=3)
            if not results:
                continue

            # Extract findings
            extracted = self._extract_findings(q_text, results, depth)

            for title, usefulness, threads in extracted:
                surprise = self.brain.record(predicted, usefulness, q_text)
                bangs = usefulness_to_bangs(usefulness, surprise)

                finding = Finding(
                    title=title[:30],
                    content=results[0].content[:200] if results else "",
                    url=results[0].url if results else "",
                    usefulness=usefulness,
                    predicted=predicted,
                    surprise=surprise,
                    bangs=bangs,
                    depth=depth,
                    threads=threads,
                )
                findings.append(finding)

                if usefulness >= 0.6:
                    n_useful += 1
                if surprise > 0.5:
                    n_surprise += 1
                if bangs:
                    brain_gained += len(bangs)

                # Learn from high-surprise findings
                if surprise > 0.7 and usefulness > 0.6:
                    self.brain.learn(
                        f"High-value unexpected: '{title}' from query about "
                        f"'{topics[0][:30]}' at depth {depth}"
                    )

                all_threads.extend(threads)

                if on_finding:
                    on_finding(finding, len(findings), depth)

        return DepthResult(
            depth=depth,
            findings=findings,
            n_searched=len(queries),
            n_useful=n_useful,
            n_surprise=n_surprise,
            brain_gained=brain_gained,
            threads=all_threads,
        )

    def _generate_queries(self, topics: List[str], depth: int) -> List[tuple]:
        """Generate search queries with predicted usefulness.

        Generates more queries than needed, then ranks by expected value
        to pick the best ones to explore.
        """
        # Generate extra candidates, then filter by expected value
        n = max(3, self.queries_per_depth - depth)
        n_candidates = n + 3  # generate extras for ranking
        topic_str = ", ".join(topics)

        context_parts = []
        if self.brain.data["learnings"]:
            context_parts.append("Past learnings:\n" + "\n".join(
                f"- {l}" for l in self.brain.data["learnings"][-5:]
            ))

        # Inject best strategies into query generation
        best_strats = self.brain.best_strategies(3)
        if best_strats:
            context_parts.append(
                "Effective search strategies: " + ", ".join(best_strats)
            )

        # Inject topic prior
        prior = self.brain.get_prior(topic_str)
        if prior != 0.5:
            context_parts.append(
                f"Prior expectation for this topic area: {prior:.2f} usefulness"
            )

        context = "\n".join(context_parts)

        prompt = QUERY_PROMPT.format(
            n=n_candidates, topic=topic_str, depth=depth, context=context
        )

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1000,
            )
            text = response.choices[0].message.content.strip()
            data = _parse_json(text)

            candidates = [
                (q["q"], float(q.get("p", 0.5)))
                for q in data.get("queries", [])
            ]

            if len(candidates) <= n:
                if self.verbose:
                    for q_text, predicted in candidates:
                        explain = self.brain.query_value_explain(q_text, predicted)
                        explain["query"] = q_text
                        explain["selected"] = True
                        self.query_explanations.append(explain)
                return candidates

            # Rank by expected value — pick queries that maximize
            # uncertainty reduction + predicted usefulness
            scored = []
            for q_text, predicted in candidates:
                if self.verbose:
                    explain = self.brain.query_value_explain(q_text, predicted)
                    explain["query"] = q_text
                    scored.append((q_text, predicted, explain["score"], explain))
                else:
                    value = self.brain.query_value(q_text, predicted)
                    scored.append((q_text, predicted, value, None))

            scored.sort(key=lambda x: x[2])  # lower = better
            selected = scored[:n]

            if self.verbose:
                selected_queries = {s[0] for s in selected}
                for _, _, _, explain in scored:
                    if explain:
                        explain["selected"] = explain["query"] in selected_queries
                        self.query_explanations.append(explain)

            return [(q, p) for q, p, _, _ in selected]

        except Exception:
            return [(t, 0.5) for t in topics[:n]]

    def _extract_findings(
        self,
        query: str,
        results: List[SearchResult],
        depth: int,
    ) -> List[tuple]:
        """Extract structured findings from search results."""
        results_text = "\n\n".join(
            f"[{r.title}]({r.url})\n{r.content[:500]}"
            for r in results
        )

        prompt = EXTRACT_PROMPT.format(topic=query, results=results_text)

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000,
            )
            text = response.choices[0].message.content.strip()
            data = _parse_json(text)

            return [
                (
                    f["title"],
                    float(f.get("usefulness", 0.5)),
                    f.get("threads", []),
                )
                for f in data.get("findings", [])
            ]
        except Exception:
            # Fallback: use search results directly
            return [
                (r.title[:30], r.score or 0.5, [])
                for r in results[:2]
            ]


def format_shareable(topic: str, results: List[DepthResult], brain_summary: str) -> str:
    """Generate a clean, shareable markdown summary of research results."""
    lines: List[str] = [f"# why: {topic}", ""]

    total_findings = 0
    useful_count = 0
    surprise_count = 0
    all_threads: List[str] = []

    for dr in results:
        lines.append(f"## Depth {dr.depth}")
        lines.append("")

        sorted_findings = sorted(dr.findings, key=lambda f: f.usefulness, reverse=True)
        for f in sorted_findings:
            total_findings += 1
            if f.usefulness >= 0.6:
                useful_count += 1
            if f.surprise > 0.5:
                surprise_count += 1
            line = f"- **{f.title}** {f.bangs} — {f.content[:150]}"
            lines.append(line)
            if f.url:
                lines.append(f"  {f.url}")

        lines.append("")
        all_threads.extend(dr.threads)

    lines.append("---")
    lines.append(
        f"*{total_findings} findings · {useful_count} useful · "
        f"{surprise_count} surprises · brain: {brain_summary}*"
    )
    top_threads = all_threads[:5]
    n_threads = len(all_threads)
    lines.append(
        f"*{n_threads} threads to explore: {', '.join(top_threads)}*"
    )

    return "\n".join(lines)


def format_shareable_compact(topic: str, results: List[DepthResult]) -> str:
    """Generate a super compact summary for social sharing / terminal screenshot."""
    lines: List[str] = [f"why {topic}", ""]

    # Collect all findings across depths, sort by usefulness
    all_findings: List[Finding] = []
    for dr in results:
        all_findings.extend(dr.findings)
    all_findings.sort(key=lambda f: f.usefulness, reverse=True)

    total = len(all_findings)
    useful = sum(1 for f in all_findings if f.usefulness >= 0.6)
    surprises = sum(1 for f in all_findings if f.surprise > 0.5)

    top = all_findings[:8]
    if top:
        max_title_len = max(len(f.title) for f in top)
        for f in top:
            padding = " " * (max_title_len - len(f.title) + 2)
            lines.append(f"  {f.title}{padding}{f.bangs}")

    lines.append("")
    lines.append(f"{total}\u00b7{useful}\u2726\u00b7{surprises}!")

    return "\n".join(lines)


def research_confidence(results: List[DepthResult], brain: Brain) -> Dict[str, Any]:
    """Compute aggregate confidence in research results.

    Considers: finding agreement, calibration, source diversity,
    surprise distribution, and depth coverage.

    Returns a score 0-1 and a breakdown of contributing factors.
    """
    all_findings = []
    for dr in results:
        all_findings.extend(dr.findings)

    if not all_findings:
        return {"confidence": 0.0, "reason": "no findings", "breakdown": {}}

    n = len(all_findings)

    # 1. Usefulness consistency — are findings mostly useful or mixed?
    usefulness_scores = [f.usefulness for f in all_findings]
    mean_usefulness = sum(usefulness_scores) / n
    usefulness_variance = sum((u - mean_usefulness) ** 2 for u in usefulness_scores) / n
    consistency = max(0, 1.0 - usefulness_variance * 4)  # low variance = high consistency

    # 2. Calibration — how well-calibrated is the brain on these topics?
    cal = brain.calibration

    # 3. Source diversity — how many unique sources?
    urls = set(f.url for f in all_findings if f.url)
    source_diversity = min(len(urls) / max(n, 1), 1.0)

    # 4. Surprise balance — some surprise is good (found non-obvious), all surprise is bad (unstable)
    surprises = [f.surprise for f in all_findings]
    mean_surprise = sum(surprises) / n
    if mean_surprise < 0.1:
        surprise_score = 0.5  # all obvious — mediocre
    elif mean_surprise < 0.4:
        surprise_score = 0.9  # good mix — found some non-obvious
    else:
        surprise_score = 0.6  # too much surprise — potentially unreliable

    # 5. Depth coverage — did we go deep?
    depths_covered = len(results)
    depth_score = min(depths_covered / 3, 1.0)

    # Weighted combination
    confidence = (
        consistency * 0.25
        + cal * 0.25
        + source_diversity * 0.15
        + surprise_score * 0.20
        + depth_score * 0.15
    )

    return {
        "confidence": round(confidence, 3),
        "breakdown": {
            "consistency": round(consistency, 3),
            "calibration": round(cal, 3),
            "source_diversity": round(source_diversity, 3),
            "surprise_balance": round(surprise_score, 3),
            "depth_coverage": round(depth_score, 3),
        },
        "findings": n,
        "unique_sources": len(urls),
        "mean_usefulness": round(mean_usefulness, 3),
    }


def _parse_json(text: str) -> dict:
    if "```" in text:
        for block in text.split("```")[1::2]:
            clean = block.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            try:
                return json.loads(clean)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {}
