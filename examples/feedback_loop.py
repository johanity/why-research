"""Feedback loop example — teach the brain from human judgment."""

from why.engine import Engine
from why.brain import Brain

brain = Brain()
engine = Engine(brain=brain, max_depth=0, queries_per_depth=3)

# Research a topic
results = engine.run("benefits of intermittent fasting")

print("--- Findings ---")
for dr in results:
    for f in dr.findings:
        print(f"\n  {f.title}")
        print(f"  LLM rated usefulness: {f.usefulness:.2f}")
        print(f"  ID: {f.id}")

# Simulate human feedback
# In real use, this comes from user interaction (CLI: y/n, or MCP: research_feedback)
print("\n--- Giving Feedback ---")

# Mark some findings as useful/not useful
brain.feedback("finding_1", True, "benefits of intermittent fasting")
print("  + Marked finding_1 as useful")

brain.feedback("finding_2", False, "benefits of intermittent fasting")
print("  - Marked finding_2 as not useful")

# Check how the brain adapted
prior_before = "unknown"
prior_after = brain.get_prior("benefits intermittent fasting")
print(f"\n--- Brain Adapted ---")
print(f"  Prior for this topic: {prior_after:.2f}")
print(f"  Feedback recorded: {brain.data.get('feedback_n', 0)}")
print(f"  Feedback useful rate: {brain.data.get('feedback_useful', 0) / max(brain.data.get('feedback_n', 1), 1):.0%}")
