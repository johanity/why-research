"""why — the CLI.

Usage:
    why swarms              # one-shot research
    why                     # interactive mode
    why --brain             # check brain state
    why --serve             # start MCP server
    why --api               # start hosted API
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from .brain import Brain
from .display import (
    render_depth_end,
    render_depth_start,
    render_file,
    render_finding,
    render_stats,
    render_threads,
    _slow,
)
from .engine import Engine, Finding, DepthResult


def _run_research(topic: str, brain: Brain, engine: Engine) -> list:
    """Run research on a topic with live diamond rendering. Returns threads."""
    cumulative = {
        "found": 0,
        "useful": 0,
        "surprise": 0,
        "brain": brain.level,
    }
    all_threads: list = []
    depth_finding_counts: dict = {}

    def on_depth_start(depth: int) -> None:
        depth_finding_counts[depth] = 0
        render_depth_start(depth)

    def on_finding(finding: Finding, index: int, depth: int) -> None:
        depth_finding_counts[depth] = depth_finding_counts.get(depth, 0) + 1
        estimated_total = max(depth_finding_counts[depth], engine.queries_per_depth - depth)
        render_finding(finding, depth_finding_counts[depth] - 1, estimated_total, depth)

        cumulative["found"] += 1
        if finding.usefulness >= 0.6:
            cumulative["useful"] += 1
        if finding.surprise > 0.5:
            cumulative["surprise"] += 1
        if finding.bangs:
            cumulative["brain"] += len(finding.bangs)

        all_threads.extend(finding.threads)

    def on_depth_end(depth: int, result: DepthResult) -> None:
        render_depth_end(depth, result, cumulative)

    render_finding_topic(topic)

    results = engine.run(
        topic,
        on_finding=on_finding,
        on_depth_start=on_depth_start,
        on_depth_end=on_depth_end,
    )

    render_stats(
        cumulative["found"],
        cumulative["useful"],
        cumulative["surprise"],
        brain.level,
    )

    # Save report
    safe_name = "".join(c if c.isalnum() or c in "- " else "_" for c in topic)
    safe_name = safe_name.replace(" ", "_")[:40].lower()
    filename = f"{safe_name}.md"

    report_lines = [f"# why {topic}\n"]
    for dr in results:
        report_lines.append(f"\n## depth {dr.depth}\n")
        for f in dr.findings:
            bangs = f" {f.bangs}" if f.bangs else ""
            report_lines.append(f"- **{f.title}**{bangs}")
            if f.content:
                report_lines.append(f"  {f.content[:200]}")
            if f.url:
                report_lines.append(f"  [{f.url}]({f.url})")
            report_lines.append("")

    if all_threads:
        report_lines.append("\n## threads to pull\n")
        for t in all_threads[:10]:
            report_lines.append(f"- {t}")

    report_path = Path(filename)
    report_path.write_text("\n".join(report_lines))
    render_file(filename)

    return list(set(all_threads))


def render_finding_topic(topic: str) -> None:
    """Render the topic header."""
    from .display import render_topic
    render_topic(topic)


def _show_brain(brain: Brain) -> None:
    """Display brain state."""
    print()
    _slow(f"  brain level {brain.level}", delay=0.03)
    _slow(f"  {brain.summary()}", delay=0.02)
    if brain.data["learnings"]:
        print()
        _slow("  recent learnings:", delay=0.03)
        for l in brain.data["learnings"][-5:]:
            _slow(f"    · {l[:60]}", delay=0.015)
    print()


def _interactive(brain: Brain) -> None:
    """Interactive REPL — the agent mode."""
    engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
    pending_threads: list = []

    print()
    _slow("why", delay=0.08)
    _slow(f"  brain level {brain.level} · {brain.data['sessions']} sessions", delay=0.025)
    print()

    while True:
        try:
            sys.stdout.write("  → ")
            sys.stdout.flush()
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _slow("  ·", delay=0.05)
            break

        if not line:
            continue

        if line in ("q", "quit", "exit"):
            _slow("  ·", delay=0.05)
            break

        if line in ("brain", "b", "status"):
            _show_brain(brain)
            continue

        if line.startswith("y ") or line.startswith("n "):
            # Feedback: y <finding_text> or n <finding_text>
            useful = line[0] == "y"
            query = line[2:].strip()
            result = brain.feedback("cli", useful, query)
            symbol = "+" if useful else "-"
            _slow(f"  {symbol} recorded (total: {result['total_feedback']})", delay=0.02)
            continue

        if line in ("threads", "t"):
            if pending_threads:
                print()
                for i, t in enumerate(pending_threads[:9], 1):
                    _slow(f"  {i}. {t}", delay=0.02)
                print()
            else:
                _slow("  no threads yet", delay=0.03)
            continue

        # Number = pick a thread
        if line.isdigit() and pending_threads:
            idx = int(line) - 1
            if 0 <= idx < len(pending_threads):
                line = pending_threads[idx]
                pending_threads.pop(idx)
            else:
                _slow("  invalid thread number", delay=0.03)
                continue

        if line.startswith("explain "):
            topic = line[8:]
            engine_explain = Engine(brain=brain, max_depth=0, queries_per_depth=4, verbose=True)
            _run_research(topic, brain, engine_explain)
            if engine_explain.query_explanations:
                print()
                sorted_exp = sorted(engine_explain.query_explanations, key=lambda x: x.get("score", 0))
                for exp in sorted_exp:
                    sel = "→" if exp.get("selected") else " "
                    q = exp.get("query", "")[:50]
                    score = exp.get("score", 0)
                    cat = exp.get("category", "")
                    prior = exp.get("prior", 0.5)
                    ep = exp.get("epistemic_value", 0)
                    pg = exp.get("pragmatic_value", 0)
                    strat = exp.get("strategy", "")
                    sr = exp.get("strategy_success_rate")
                    sr_str = f"{sr:.0%}" if sr is not None else "n/a"
                    _slow(f"  {sel} {q}", delay=0.015)
                    _slow(f"      score:{score:.3f}  prior:{prior:.2f}  epistemic:{ep:.2f}  pragmatic:{pg:.2f}", delay=0.01)
                    _slow(f"      cat:{cat}  strat:{strat}({sr_str})", delay=0.01)
                print()
            continue

        if line.startswith("deep "):
            topic = line[5:]
            engine_deep = Engine(brain=brain, max_depth=3, queries_per_depth=8)
            new_threads = _run_research(topic, brain, engine_deep)
            pending_threads = new_threads[:15]
        elif line.startswith("quick "):
            topic = line[6:]
            engine_quick = Engine(brain=brain, max_depth=0, queries_per_depth=3)
            new_threads = _run_research(topic, brain, engine_quick)
            pending_threads = new_threads[:10]
        else:
            new_threads = _run_research(line, brain, engine)
            pending_threads = new_threads[:12]

        remaining = len(pending_threads)
        if remaining > 0:
            render_threads(min(remaining, 9))


def main() -> None:
    # Flags
    if "--brain" in sys.argv:
        brain = Brain()
        _show_brain(brain)
        return

    if "--serve" in sys.argv:
        from .server import run_server
        run_server()
        return

    if "--api" in sys.argv:
        from .api import run_api
        run_api()
        return

    if "-h" in sys.argv or "--help" in sys.argv:
        print("why — ask why. get answers. get smarter.")
        print()
        print("usage:")
        print("  why                    interactive mode")
        print("  why <anything>         one-shot research")
        print("  why --brain            check brain state")
        print("  why --serve            start MCP server")
        print("  why --api              start hosted API")
        print()
        print("interactive commands:")
        print("  <topic>                research a topic")
        print("  deep <topic>           deeper research (3 levels)")
        print("  quick <topic>          fast surface scan")
        print("  explain <topic>        show why queries are ranked")
        print("  threads / t            show pending threads")
        print("  <number>               follow a thread")
        print("  y <topic>              mark last finding useful")
        print("  n <topic>              mark last finding not useful")
        print("  brain / b              check brain state")
        print("  quit / q               exit")
        return

    brain = Brain()

    # No args = interactive mode
    if len(sys.argv) < 2:
        _interactive(brain)
        return

    # One-shot mode
    topic = " ".join(sys.argv[1:])
    engine = Engine(brain=brain, max_depth=2, queries_per_depth=6)
    threads = _run_research(topic, brain, engine)

    remaining = len(threads)
    if remaining > 0:
        render_threads(min(remaining, 9))


if __name__ == "__main__":
    main()
