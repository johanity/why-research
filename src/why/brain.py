"""Persistent learning — why gets smarter every time you use it.

Tracks prediction accuracy, topic priors, and strategy effectiveness
across sessions using online statistical methods.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List


class Brain:
    """Accumulated research intelligence across all sessions.

    Maintains priors over topic categories, tracks prediction accuracy,
    and generates anticipatory queries ranked by expected value.

    Tracks prediction accuracy, topic priors, and strategy effectiveness.
    """

    def __init__(self, path: str = "~/.why") -> None:
        self.path = Path(path).expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.file = self.path / "brain.json"
        self.data = self._load()

    def _init_data(self) -> Dict[str, Any]:
        """Return the initial data schema."""
        return {
            "sessions": 0,
            "total_searches": 0,
            "total_useful": 0,
            "total_surprises": 0,
            "patterns_learned": 0,
            "calibration_n": 0,
            "calibration_sum_error": 0.0,
            "learnings": [],
            "priors": {},
            "session_uncertainty_reduced": 0.0,
            "strategies": {},
        }

    def _load(self) -> Dict[str, Any]:
        if self.file.exists():
            return json.loads(self.file.read_text())
        return self._init_data()

    def save(self) -> None:
        self.file.write_text(json.dumps(self.data, indent=2))

    def start_session(self) -> None:
        self.data["sessions"] += 1
        self.data["session_uncertainty_reduced"] = 0.0

    def record(self, predicted: float, actual: float, query: str) -> float:
        """Record a prediction vs actual. Returns surprise score (0-1)."""
        error = abs(predicted - actual)
        self.data["total_searches"] += 1
        self.data["calibration_n"] += 1
        self.data["calibration_sum_error"] += error

        if actual >= 0.6:
            self.data["total_useful"] += 1

        # Simple surprise: clamp error-based score to 0-1
        surprise = min(error * 2, 1.0)

        if surprise > 0.5:
            self.data["total_surprises"] += 1

        # Update topic priors
        category = self._categorize_query(query)
        prior = self.data["priors"].get(category, {"mean": 0.5, "n": 0, "sum": 0.0})
        prior["n"] += 1
        prior["sum"] += actual
        prior["mean"] = prior["sum"] / prior["n"]
        self.data["priors"][category] = prior

        # Uncertainty reduced = surprise that led to learning
        if surprise > 0.3:
            self.data["session_uncertainty_reduced"] += surprise * actual

        # Track strategy effectiveness
        strategy = self._extract_strategy(query)
        strat = self.data["strategies"].get(strategy, {"n": 0, "useful": 0})
        strat["n"] += 1
        if actual >= 0.6:
            strat["useful"] += 1
        self.data["strategies"][strategy] = strat

        self.save()
        return surprise

    def learn(self, pattern: str) -> None:
        """Add a learned pattern."""
        if pattern not in self.data["learnings"]:
            self.data["learnings"].append(pattern)
            self.data["patterns_learned"] = len(self.data["learnings"])
            self.save()

    def get_prior(self, topic: str) -> float:
        """Get the brain's prior expectation for a topic category."""
        category = self._categorize_query(topic)
        prior = self.data["priors"].get(category)
        if prior and prior["n"] >= 3:
            return prior["mean"]
        return 0.5

    def query_value(self, query: str, predicted_usefulness: float) -> float:
        """Score a query by expected value.

        Combines epistemic value (uncertainty reduction) with pragmatic value
        (expected usefulness). Lower score = better query to pursue.
        """
        category = self._categorize_query(query)
        prior = self.data["priors"].get(category, {"mean": 0.5, "n": 0})

        # Epistemic value: fewer observations = more uncertainty
        n = max(prior.get("n", 0), 1)
        epistemic = 1.0 / math.sqrt(n)

        # Pragmatic value: expected usefulness based on prior + prediction
        prior_mean = prior.get("mean", 0.5)
        pragmatic = (predicted_usefulness * 0.6 + prior_mean * 0.4)

        return -(epistemic * 0.4 + pragmatic * 0.6)

    def best_strategies(self, n: int = 3) -> List[str]:
        """Return the top N most effective search strategies."""
        strategies = []
        for name, data in self.data["strategies"].items():
            if data["n"] >= 2:
                rate = data["useful"] / data["n"]
                strategies.append((name, rate, data["n"]))
        strategies.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in strategies[:n]]

    def reflect(self) -> Dict[str, Any]:
        """Structured reflection on what the brain has learned."""
        best = self.best_strategies(5)
        return {
            "calibration": round(self.calibration, 3),
            "uncertainty_reduced": round(self.data.get("session_uncertainty_reduced", 0), 3),
            "best_strategies": best,
            "total_patterns": self.data["patterns_learned"],
            "recommendation": (
                "Early stage — keep researching to build priors"
                if self.data["total_searches"] < 10
                else f"Calibration: {self.calibration:.0%}. Best strategy: {best[0] if best else 'N/A'}"
            ),
        }

    def export_delta(self) -> str:
        """Export a compact, shareable brain delta."""
        import base64
        delta = {
            "v": 1,
            "priors": self.data["priors"],
            "strategies": {k: v for k, v in self.data["strategies"].items() if v["n"] >= 3},
            "learnings": self.data["learnings"][-20:],
            "calibration": round(self.calibration, 3),
        }
        raw = json.dumps(delta, separators=(",", ":"))
        return base64.urlsafe_b64encode(raw.encode()).decode()

    def import_delta(self, encoded: str) -> int:
        """Import a brain delta from another instance. Returns patterns imported."""
        import base64
        try:
            raw = base64.urlsafe_b64decode(encoded.encode()).decode()
            delta = json.loads(raw)
        except Exception:
            return 0

        imported = 0
        for cat, their_prior in delta.get("priors", {}).items():
            my_prior = self.data["priors"].get(cat, {"mean": 0.5, "n": 0, "sum": 0.0})
            total_n = my_prior["n"] + their_prior["n"]
            if total_n > 0:
                merged_mean = (
                    my_prior["mean"] * my_prior["n"] +
                    their_prior["mean"] * their_prior["n"]
                ) / total_n
                my_prior.update({"mean": merged_mean, "n": total_n, "sum": merged_mean * total_n})
                self.data["priors"][cat] = my_prior

        for name, their_strat in delta.get("strategies", {}).items():
            my_strat = self.data["strategies"].get(name, {"n": 0, "useful": 0})
            my_strat["n"] += their_strat["n"]
            my_strat["useful"] += their_strat["useful"]
            self.data["strategies"][name] = my_strat

        for learning in delta.get("learnings", []):
            if learning not in self.data["learnings"]:
                self.data["learnings"].append(learning)
                imported += 1

        self.data["patterns_learned"] = len(self.data["learnings"])
        self.save()
        return imported

    def feedback(self, finding_id: str, useful: bool, query: str = "") -> Dict[str, Any]:
        """Record human feedback on a finding."""
        if query:
            category = self._categorize_query(query)
            prior = self.data["priors"].get(category, {"mean": 0.5, "n": 0, "sum": 0.0})
            score = 0.9 if useful else 0.2
            prior["n"] += 1
            prior["sum"] += score
            prior["mean"] = prior["sum"] / prior["n"]
            self.data["priors"][category] = prior
        self.save()
        return {"recorded": True, "total_feedback": 1}

    def _categorize_query(self, query: str) -> str:
        """Extract a rough category from a query for prior tracking."""
        words = query.lower().split()
        stop = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to",
                "for", "on", "with", "how", "what", "why", "when", "where", "does"}
        meaningful = [w for w in words if w not in stop and len(w) > 2]
        return " ".join(meaningful[:3]) if meaningful else "general"

    def _extract_strategy(self, query: str) -> str:
        """Extract the search strategy pattern from a query."""
        q = query.lower()
        matches: List[str] = []
        if "vs" in q or "versus" in q or "compared" in q:
            matches.append("comparison")
        if any(w in q for w in ["how", "mechanism", "works", "process"]):
            matches.append("mechanism")
        if any(w in q for w in ["latest", "recent", "2026", "2025", "new"]):
            matches.append("recency")
        if any(w in q for w in ["best", "top", "most", "leading"]):
            matches.append("superlative")
        if any(w in q for w in ["problem", "issue", "challenge", "limitation"]):
            matches.append("problems")
        if any(w in q for w in ["example", "case study", "use case"]):
            matches.append("examples")

        if len(matches) >= 2:
            return f"combo:{matches[0]}+{matches[1]}"
        if len(matches) == 1:
            return matches[0]
        return "general"

    @property
    def calibration(self) -> float:
        n = self.data["calibration_n"]
        if n == 0:
            return 0.0
        avg_error = self.data["calibration_sum_error"] / n
        return max(0.0, 1.0 - avg_error)

    @property
    def level(self) -> int:
        return self.data["patterns_learned"]

    def summary(self) -> str:
        d = self.data
        fe = d.get("session_uncertainty_reduced", 0)
        parts = [
            f"Sessions: {d['sessions']}",
            f"Searches: {d['total_searches']}",
            f"Useful: {d['total_useful']}",
            f"Surprises: {d['total_surprises']}",
            f"Patterns: {d['patterns_learned']}",
            f"Cal: {self.calibration:.2f}",
        ]
        if fe > 0:
            parts.append(f"UR: -{fe:.2f}")
        n_priors = len(d.get("priors", {}))
        if n_priors > 0:
            parts.append(f"Priors: {n_priors}")
        return " | ".join(parts)
