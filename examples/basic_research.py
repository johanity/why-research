"""Basic research example — run a query and inspect findings."""

from why.engine import Engine
from why.brain import Brain

brain = Brain()
engine = Engine(brain=brain, max_depth=1, queries_per_depth=4)

results = engine.run("how do transformer attention mechanisms work")

for depth_result in results:
    print(f"\n--- Depth {depth_result.depth} ---")
    print(f"Searched: {depth_result.n_searched} | Useful: {depth_result.n_useful} | Surprises: {depth_result.n_surprise}")

    for finding in depth_result.findings:
        surprise_marker = finding.bangs if finding.bangs else ""
        print(f"\n  {finding.title} {surprise_marker}")
        print(f"  Usefulness: {finding.usefulness:.2f} | Surprise: {finding.surprise:.2f}")
        if finding.url:
            print(f"  Source: {finding.url}")
        if finding.threads:
            print(f"  Threads: {finding.threads[:3]}")

print(f"\nBrain: {brain.summary()}")
